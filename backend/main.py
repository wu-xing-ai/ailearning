from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import json
from datetime import datetime
import os
import sys

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ollama_service import OllamaService
from core import OllamaConfig, StreamHandler
from ai_services import factory, AIServiceFactory

app = FastAPI(
    title="武汉外国语学校智能学习平台API",
    description="AI智能导学和智能学习系统的后端API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟数据库
class Document(BaseModel):
    id: str
    filename: str
    file_type: str
    content: str
    created_at: datetime
    processed: bool = False

class Message(BaseModel):
    id: str
    role: str  # 'user', 'assistant'
    content: str
    timestamp: datetime

class ChatSession(BaseModel):
    id: str
    title: str
    messages: List[Message] = []
    created_at: datetime
    updated_at: datetime

# 内存存储
documents_db = {}
chat_sessions = {}

# 初始化Ollama服务
ollama_config = OllamaConfig()
ollama_service = OllamaService(
    model_name=ollama_config.model,
    base_url=ollama_config.base_url
)

# 初始化AI服务工厂
ai_factory = AIServiceFactory(default_provider="ollama")

# 存储API密钥和自定义配置
api_keys_storage = {}

# API端点
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/documents")
async def upload_document(doc: dict):
    """上传文档到知识库"""
    doc_id = str(uuid.uuid4())
    document = Document(
        id=doc_id,
        filename=doc['filename'],
        file_type=doc['file_type'],
        content=doc['content'],
        created_at=datetime.now(),
        processed=False
    )
    documents_db[doc_id] = document.dict()
    return {"id": doc_id, "status": "uploaded"}

@app.get("/api/documents")
async def get_documents():
    """获取所有文档"""
    return list(documents_db.values())

@app.post("/api/chat/session")
async def create_chat_session():
    """创建新的聊天会话"""
    session_id = str(uuid.uuid4())
    session = ChatSession(
        id=session_id,
        title=f"会话 {len(chat_sessions) + 1}",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    chat_sessions[session_id] = session.dict()
    return {"id": session_id, "title": session.title}

@app.post("/api/chat/{session_id}/messages")
async def add_message(session_id: str, message: dict):
    """添加消息到聊天会话"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    chat_sessions[session_id]['messages'].append({
        "id": str(uuid.uuid4()),
        "role": message['role'],
        "content": message['content'],
        "timestamp": datetime.now()
    })
    chat_sessions[session_id]['updated_at'] = datetime.now()
    return {"status": "success"}

@app.get("/api/chat/{session_id}/messages")
async def get_messages(session_id: str):
    """获取会话中的消息"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_sessions[session_id]['messages']

@app.post("/api/ai/chat")
async def chat_with_ai(request: dict):
    """与AI对话 - 支持多厂商模型"""
    prompt = request.get("prompt", "")
    stream = request.get("stream", False)
    model_config = request.get("modelConfig", {})

    if not prompt:
        raise HTTPException(status_code=400, detail="prompt参数不能为空")

    # 确定使用哪个服务
    provider = model_config.get("type", "ollama")
    model_name = model_config.get("name", ollama_config.model)

    try:
        # 根据配置获取或创建服务
        if provider == "ollama":
            # 使用Ollama服务
            service = ollama_service
            if model_name != service.model_name:
                service.update_model(model_name)
        elif provider == "custom":
            # 使用自定义API
            service = factory.create_service(
                provider="custom",
                model_name=model_name,
                api_key=model_config.get("apiKey"),
                api_url=model_config.get("apiUrl")
            )
        else:
            # 使用其他厂商服务
            api_key = model_config.get("apiKey") or api_keys_storage.get(provider)
            if not api_key and provider != "ollama":
                raise HTTPException(
                    status_code=400,
                    detail=f"请先配置{provider}的API密钥"
                )

            service = factory.create_service(
                provider=provider,
                model_name=model_name,
                api_key=api_key,
                api_url=model_config.get("apiUrl")
            )

        if stream:
            # 流式响应
            generator = service.chat_completion(prompt, stream=True)
            return StreamHandler.create_stream(generator)
        else:
            # 非流式响应
            response = await service.chat_completion(prompt, stream=False)
            if "error" in response:
                raise HTTPException(status_code=500, detail=response["error"])
            return {
                "response": response["response"],
                "model": response.get("model", service.model_name),
                "provider": provider,
                "timestamp": datetime.now().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI服务错误: {str(e)}")


# ==================== AI配置管理端点 ====================

@app.get("/api/ai/config")
async def get_ai_config():
    """获取当前AI配置"""
    config = ollama_config.get_config()
    config["supported_providers"] = ai_factory.get_supported_providers()
    return config


@app.put("/api/ai/config")
async def update_ai_config(config: dict):
    """更新AI配置"""
    success = ollama_config.save_config(config)
    if success:
        # 更新服务实例
        if "model" in config:
            ollama_service.update_model(config["model"])
        if "base_url" in config:
            ollama_service.update_base_url(config["base_url"])

        # 更新API密钥存储
        if "apiKeys" in config:
            for provider, key in config["apiKeys"].items():
                if key:
                    api_keys_storage[provider] = key
                    ai_factory.register_api_key(provider, key)

        return {"status": "updated", "config": ollama_config.get_config()}
    raise HTTPException(status_code=500, detail="配置保存失败")


@app.post("/api/ai/api-keys")
async def set_api_key(request: dict):
    """设置厂商API密钥"""
    provider = request.get("provider")
    api_key = request.get("apiKey")

    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="provider和apiKey参数不能为空")

    # 存储API密钥
    api_keys_storage[provider] = api_key
    ai_factory.register_api_key(provider, api_key)

    return {"status": "success", "provider": provider}


@app.delete("/api/ai/api-keys/{provider}")
async def delete_api_key(provider: str):
    """删除厂商API密钥"""
    if provider in api_keys_storage:
        del api_keys_storage[provider]
    return {"status": "deleted", "provider": provider}


@app.post("/api/ai/reset")
async def reset_ai_context():
    """重置对话上下文"""
    ollama_service.reset_context()
    # 清除所有缓存的服务实例
    ai_factory.clear_services()
    return {"status": "reset", "message": "对话上下文已重置"}


@app.get("/api/ai/models")
async def get_available_models():
    """获取可用的模型列表"""
    current_provider = ollama_config.get_config().get("provider", "ollama")

    try:
        models = []
        if current_provider == "ollama":
            models = await ollama_service.get_available_models()
        elif current_provider == "siliconflow":
            models = [
                {"value": "Qwen/Qwen2.5-7B-Instruct", "label": "Qwen2.5 7B (免费)"},
                {"value": "Qwen/Qwen2.5-72B-Instruct", "label": "Qwen2.5 72B"},
                {"value": "deepseek-ai/DeepSeek-V2.5", "label": "DeepSeek V2.5"},
                {"value": "THUDM/glm-4-9b-chat", "label": "GLM-4 9B (免费)"},
                {"value": "meta-llama/Meta-Llama-3.1-8B-Instruct", "label": "Llama 3.1 8B"}
            ]

        return {
            "models": models,
            "current": ollama_config.get_config().get("model", ollama_service.model_name),
            "provider": current_provider
        }
    except Exception as e:
        # 如果获取失败，返回默认模型列表
        return {
            "models": ["llama3.2", "llama3.1", "mistral", "qwen2"],
            "current": ollama_service.model_name,
            "provider": "ollama",
            "error": f"无法获取模型列表: {str(e)}"
        }


@app.get("/api/ai/models/{provider}")
async def get_provider_models(provider: str):
    """获取指定厂商的模型列表"""
    try:
        if provider == "ollama":
            models = await ollama_service.get_available_models()
        else:
            # 创建临时服务实例获取模型列表
            api_key = api_keys_storage.get(provider)
            service = factory.create_service(
                provider=provider,
                model_name="default",
                api_key=api_key
            )
            models = await service.get_available_models()

        return {"models": models, "provider": provider}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取{provider}模型列表失败: {str(e)}"
        )


@app.get("/api/ai/context")
async def get_conversation_context():
    """获取当前对话上下文"""
    return {"context": ollama_service.get_context()}


@app.get("/api/ai/context")
async def get_conversation_context():
    """获取当前对话上下文"""
    return {"context": ollama_service.get_context()}


@app.post("/api/ai/config/reset")
async def reset_to_default_config():
    """重置为默认配置"""
    success = ollama_config.reset_config()
    if success:
        ollama_service.update_model(ollama_config.model)
        ollama_service.update_base_url(ollama_config.base_url)
        # 清除API密钥
        api_keys_storage.clear()
        ai_factory.clear_services()
        return {"status": "reset", "config": ollama_config.get_config()}
    raise HTTPException(status_code=500, detail="配置重置失败")


@app.get("/api/ai/providers")
async def get_supported_providers():
    """获取支持的AI厂商列表"""
    providers = ai_factory.get_supported_providers()
    provider_info = {
        "ollama": {
            "name": "Ollama本地模型",
            "requires_api_key": False,
            "default_models": ["llama3.2", "llama3.1", "mistral", "qwen2"]
        },
        "openai": {
            "name": "OpenAI (GPT)",
            "requires_api_key": True,
            "default_models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        },
        "anthropic": {
            "name": "Anthropic (Claude)",
            "requires_api_key": True,
            "default_models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        },
        "zhipu": {
            "name": "智谱AI (GLM)",
            "requires_api_key": True,
            "default_models": ["glm-4", "glm-4-air", "glm-3-turbo"]
        },
        "qwen": {
            "name": "阿里通义千问",
            "requires_api_key": True,
            "default_models": ["qwen-turbo", "qwen-plus", "qwen-max"]
        },
        "custom": {
            "name": "自定义API",
            "requires_api_key": True,
            "default_models": []
        }
    }

    return {
        "providers": providers,
        "info": {k: v for k, v in provider_info.items() if k in providers}
    }

@app.post("/api/knowledge/process")
async def process_knowledge(doc_id: str = Query(..., description="文档ID")):
    """处理知识库文档"""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")

    # 模拟文档处理
    documents_db[doc_id]['processed'] = True
    return {"status": "processing", "document_id": doc_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)