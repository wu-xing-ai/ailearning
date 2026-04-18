from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import json
from datetime import datetime
import os
import sys
import shutil
from urllib.parse import unquote
from sqlalchemy import text

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ollama_service import OllamaService
from core import OllamaConfig, StreamHandler
from core.database import get_db, init_db, engine
from ai_services import factory, AIServiceFactory
from services.document_processor import DocumentProcessor
from services.knowledge_processor import STRUCTURE_VERSION, build_structure, dumps_json
from services.ai_knowledge_processor import STRUCTURE_VERSION_AI, PROMPT_VERSION, build_ai_structure
from services.embedding_service import embedding_service
from services.hybrid_search import hybrid_search
from services.progress_service import ProgressService
from models.user import User as UserModel
from models.chat_session import ChatSessionDB, ChatMessageDB
from core.auth import (
    hash_password, verify_password, create_access_token, decode_access_token,
    get_current_user, require_auth, require_role,
)
from models.document import Document as DocumentModel
from models.document_chunk import DocumentChunk
from models.document_structure import DocumentStructure

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

# 内存存储（仅用于聊天会话等临时数据）
chat_sessions = {}

# API密钥存储
api_keys_storage = {}

# 自定义模型存储文件路径
CUSTOM_MODELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_models.json")

def load_custom_models():
    """加载自定义模型配置"""
    if os.path.exists(CUSTOM_MODELS_FILE):
        try:
            with open(CUSTOM_MODELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_custom_models(models):
    """保存自定义模型配置"""
    with open(CUSTOM_MODELS_FILE, "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    print("数据库初始化完成")

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
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库"""
    from sqlalchemy.orm import Session

    # 处理文件名编码（支持中文文件名）
    filename = file.filename
    try:
        # 修复 Windows curl 等工具造成的编码问题
        # 中文 UTF-8 字节被错误地解释为 latin-1，需要反转这个过程
        filename_bytes = filename.encode('latin-1')
        filename = filename_bytes.decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    except Exception:
        pass

    # 1. 验证文件类型
    file_type = DocumentProcessor.get_file_type(filename)
    if file_type == 'unknown':
        raise HTTPException(status_code=400, detail="不支持的文件格式，仅支持 PDF、DOCX、TXT、XLSX、MD")

    # 2. 读取文件内容
    content_bytes = await file.read()

    # 3. 提取文本内容
    try:
        text_content, file_type_name = DocumentProcessor.extract_content(
            content_bytes, file_type, filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

    # 4. 生成文档ID
    doc_id = str(uuid.uuid4())

    # 5. 保存原始文件到 knowledge_base 目录
    knowledge_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
    doc_dir = os.path.join(knowledge_base_dir, doc_id)
    os.makedirs(doc_dir, exist_ok=True)

    file_path = os.path.join(doc_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    # 6. 保存到数据库
    db = next(get_db())
    try:
        document = DocumentModel(
            id=doc_id,
            filename=filename,
            file_type=file_type_name,
            content=text_content,
            file_path=file_path,
            processed=False
        )
        db.add(document)
        db.commit()
    finally:
        db.close()

    return {
        "id": doc_id,
        "status": "uploaded",
        "filename": filename,
        "file_type": file_type_name,
        "file_path": file_path
    }

@app.get("/api/documents")
async def get_documents():
    """获取所有文档"""
    from sqlalchemy.orm import Session

    db = next(get_db())
    try:
        documents = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
        return JSONResponse(
            content=[doc.to_dict() for doc in documents],
            media_type="application/json; charset=utf-8"
        )
    finally:
        db.close()

@app.get("/api/documents/search")
async def search_documents(q: str = Query(..., description="搜索关键词")):
    """搜索文档"""
    from sqlalchemy.orm import Session

    if not q or not q.strip():
        return []

    db = next(get_db())
    try:
        search_term = f"%{q.strip()}%"
        documents = db.query(DocumentModel).filter(
            (DocumentModel.filename.like(search_term)) |
            (DocumentModel.content.like(search_term))
        ).order_by(DocumentModel.created_at.desc()).all()

        results = []
        for doc in documents:
            # 提取内容摘要（包含关键词的前后100字符）
            content = doc.content or ""
            keyword = q.strip().lower()
            content_lower = content.lower()
            idx = content_lower.find(keyword)

            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(content), idx + len(keyword) + 50)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
            else:
                snippet = content[:100] + "..." if len(content) > 100 else content

            results.append({
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "snippet": snippet,
                "processed": doc.processed,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            })

        return results
    finally:
        db.close()

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    knowledge_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
    doc_dir = os.path.join(knowledge_base_dir, doc_id)

    try:
        with engine.begin() as conn:
            exists = conn.execute(text("SELECT id FROM documents WHERE id = :doc_id"), {"doc_id": doc_id}).fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="文档不存在")

            conn.execute(text("DELETE FROM document_chunks WHERE document_id = :doc_id"), {"doc_id": doc_id})
            conn.execute(text("DELETE FROM document_structures WHERE document_id = :doc_id"), {"doc_id": doc_id})
            conn.execute(text("DELETE FROM documents WHERE id = :doc_id"), {"doc_id": doc_id})

        if os.path.exists(doc_dir):
            shutil.rmtree(doc_dir)

        # Clean up ChromaDB vectors
        try:
            embedding_service.delete_document(doc_id)
        except Exception:
            pass

        return {"status": "deleted", "id": doc_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")

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
            # 流式响应 - await获取async generator
            result = service.chat_completion(prompt, stream=True)
            # 如果是coroutine，需要await
            import inspect
            if inspect.iscoroutine(result):
                generator = await result
            else:
                generator = result
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


# ==================== 自定义模型管理端点 ====================

@app.get("/api/ai/custom-models")
async def get_custom_models():
    """获取所有自定义模型"""
    models = load_custom_models()
    return {"models": models}


@app.post("/api/ai/custom-models")
async def add_custom_model(request: dict):
    """添加自定义模型"""
    name = request.get("name")
    api_url = request.get("apiUrl")
    api_key = request.get("apiKey", "")

    if not name or not api_url:
        raise HTTPException(status_code=400, detail="模型名称和API地址不能为空")

    models = load_custom_models()

    # 检查是否已存在
    for m in models:
        if m["name"] == name:
            # 更新现有模型
            m["api_url"] = api_url
            m["api_key"] = api_key
            save_custom_models(models)
            return {"status": "updated", "model": m}

    # 添加新模型
    new_model = {
        "name": name,
        "api_url": api_url,
        "api_key": api_key,
        "created_at": datetime.now().isoformat()
    }
    models.append(new_model)
    save_custom_models(models)

    return {"status": "created", "model": new_model}


@app.delete("/api/ai/custom-models/{model_name}")
async def delete_custom_model(model_name: str):
    """删除自定义模型"""
    models = load_custom_models()
    original_count = len(models)

    models = [m for m in models if m["name"] != model_name]

    if len(models) == original_count:
        raise HTTPException(status_code=404, detail="模型不存在")

    save_custom_models(models)
    return {"status": "deleted", "model_name": model_name}

@app.post("/api/knowledge/process")
async def process_knowledge(
    doc_id: str = Query(..., description="文档ID"),
    force: bool = Query(False, description="是否强制重新处理")
):
    """处理知识库文档（规则版结构化 v1）"""
    from sqlalchemy.orm import Session

    db = next(get_db())
    try:
        document = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        if not document.content or not document.content.strip():
            raise HTTPException(status_code=400, detail="文档内容为空，无法结构化")

        existing = db.query(DocumentStructure).filter(DocumentStructure.document_id == doc_id).first()
        if existing and existing.version == STRUCTURE_VERSION and not force:
            chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
            document.processed = True
            db.commit()
            return {
                "status": "processed",
                "document_id": doc_id,
                "version": existing.version,
                "chunks_count": chunks_count,
                "knowledge_points_count": len(json.loads(existing.knowledge_points_json)),
                "outline_nodes_count": 0,
                "cached": True,
            }

        if force:
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
            if existing:
                db.delete(existing)
            db.commit()

        chunks, outline, points = build_structure(document.content, document.filename)

        has_content = bool(outline.get("children")) or bool(points)

        for ch in chunks:
            db.add(DocumentChunk(
                document_id=doc_id,
                chunk_index=ch.index,
                text=ch.text,
                start_char=ch.start_char,
                end_char=ch.end_char,
                meta=None,
            ))

        structure = DocumentStructure(
            document_id=doc_id,
            version=STRUCTURE_VERSION,
            outline_json=dumps_json(outline),
            knowledge_points_json=dumps_json(points),
        )
        db.add(structure)

        document.processed = has_content
        db.commit()

        return {
            "status": "processed" if has_content else "empty",
            "document_id": doc_id,
            "version": STRUCTURE_VERSION,
            "chunks_count": len(chunks),
            "knowledge_points_count": len(points),
            "outline_nodes_count": _count_outline_nodes(outline),
            "cached": False,
        }
    finally:
        db.close()


@app.get("/api/knowledge/structure")
async def get_knowledge_structure(doc_id: str = Query(..., description="文档ID")):
    """获取文档结构化结果"""
    db = next(get_db())
    try:
        structure = db.query(DocumentStructure).filter(DocumentStructure.document_id == doc_id).first()
        if not structure:
            raise HTTPException(status_code=404, detail="结构化结果不存在，请先处理文档")

        return JSONResponse(
            content={
                "document_id": doc_id,
                "version": structure.version,
                "source": structure.source,
                "ai_model": structure.ai_model,
                "outline": json.loads(structure.outline_json),
                "knowledge_points": json.loads(structure.knowledge_points_json),
                "updated_at": structure.updated_at.isoformat() if structure.updated_at else None,
            },
            media_type="application/json; charset=utf-8"
        )
    finally:
        db.close()


@app.post("/api/knowledge/process-ai")
async def process_knowledge_ai(request: dict):
    """AI智能结构化处理文档"""
    doc_id = request.get("doc_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="doc_id参数不能为空")

    provider = request.get("provider", "ollama")
    model_name = request.get("model_name", ollama_config.model)
    force = request.get("force", False)

    db = next(get_db())
    try:
        document = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        if not document.content or not document.content.strip():
            raise HTTPException(status_code=400, detail="文档内容为空，无法结构化")

        existing = db.query(DocumentStructure).filter(
            DocumentStructure.document_id == doc_id,
            DocumentStructure.source == "ai",
        ).first()
        if existing and not force:
            chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
            return {
                "status": "processed",
                "document_id": doc_id,
                "version": existing.version,
                "source": "ai",
                "ai_model": existing.ai_model,
                "chunks_count": chunks_count,
                "knowledge_points_count": len(json.loads(existing.knowledge_points_json)),
                "cached": True,
            }

        if force:
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
            existing_all = db.query(DocumentStructure).filter(DocumentStructure.document_id == doc_id).all()
            for e in existing_all:
                db.delete(e)
            db.commit()

        # Create AI service
        try:
            if provider == "ollama":
                service = ollama_service
                if model_name != service.model_name:
                    from ollama_service import OllamaService as _OS
                    service = _OS(model_name=model_name, base_url=ollama_config.base_url)
            elif provider == "custom":
                service = factory.create_service(
                    provider="custom",
                    model_name=model_name,
                    api_key=request.get("api_key"),
                    api_url=request.get("api_url"),
                )
            else:
                api_key = request.get("api_key") or api_keys_storage.get(provider)
                service = factory.create_service(
                    provider=provider,
                    model_name=model_name,
                    api_key=api_key,
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"AI服务初始化失败: {str(e)}")

        chunks, outline, points = await build_ai_structure(
            service, document.content, document.filename
        )

        has_content = bool(outline.get("children")) or bool(points)

        for ch in chunks:
            db.add(DocumentChunk(
                document_id=doc_id,
                chunk_index=ch.index,
                text=ch.text,
                start_char=ch.start_char,
                end_char=ch.end_char,
                meta=None,
            ))

        ai_model_label = f"{provider}/{model_name}"
        structure = DocumentStructure(
            document_id=doc_id,
            version=STRUCTURE_VERSION_AI,
            outline_json=dumps_json(outline),
            knowledge_points_json=dumps_json(points),
            source="ai",
            ai_model=ai_model_label,
            prompt_version=PROMPT_VERSION,
        )
        db.add(structure)

        document.processed = has_content
        db.commit()

        return {
            "status": "processed" if has_content else "empty",
            "document_id": doc_id,
            "version": STRUCTURE_VERSION_AI,
            "source": "ai",
            "ai_model": ai_model_label,
            "chunks_count": len(chunks),
            "knowledge_points_count": len(points),
            "outline_nodes_count": _count_outline_nodes(outline),
            "cached": False,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI结构化处理失败: {str(e)}")
    finally:
        db.close()


def _count_outline_nodes(outline: dict) -> int:
    """Count total nodes in outline tree."""
    count = 1
    for child in outline.get("children", []):
        count += _count_outline_nodes(child)
    return count


# ==================== 向量检索端点 ====================

@app.get("/api/search/semantic")
async def semantic_search(
    q: str = Query(..., description="搜索关键词"),
    mode: str = Query("hybrid", description="搜索模式: keyword/semantic/hybrid"),
    top_k: int = Query(10, description="返回结果数量"),
    doc_ids: str = Query(None, description="文档ID列表，逗号分隔"),
):
    """语义/混合搜索"""
    if not q or not q.strip():
        return {"results": [], "mode": mode, "total": 0}

    id_list = None
    if doc_ids:
        id_list = [d.strip() for d in doc_ids.split(",") if d.strip()]

    db = next(get_db())
    try:
        result = hybrid_search(db, q.strip(), mode=mode, top_k=top_k, doc_ids=id_list)
        return JSONResponse(
            content=result,
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
    finally:
        db.close()


@app.post("/api/embeddings/index")
async def index_embeddings(request: dict):
    """为指定文档生成向量嵌入"""
    doc_id = request.get("doc_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="doc_id参数不能为空")

    db = next(get_db())
    try:
        document = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
        if not chunks:
            raise HTTPException(status_code=400, detail="文档暂无分块，请先进行知识结构化处理")

        indexed = embedding_service.index_document_chunks(doc_id, chunks)

        for ch in chunks:
            ch.embedding_id = f"{doc_id}_{ch.index}"
            ch.embedding_status = "embedded"
        db.commit()

        return {"status": "indexed", "doc_id": doc_id, "chunks_indexed": indexed}
    except HTTPException:
        raise
    except Exception as e:
        # Mark chunks as failed
        try:
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
            for ch in chunks:
                ch.embedding_status = "failed"
            db.commit()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"嵌入索引失败: {str(e)}")
    finally:
        db.close()


@app.get("/api/embeddings/stats")
async def get_embedding_stats():
    """获取嵌入服务状态"""
    return embedding_service.get_stats()


# ==================== 用户认证端点 ====================

@app.post("/api/auth/register")
async def register(request: dict):
    """用户注册"""
    username = request.get("username", "").strip()
    password = request.get("password", "")
    display_name = request.get("display_name", "").strip()
    email = request.get("email", "").strip() or None
    role = request.get("role", "student")

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    if len(username) < 2 or len(username) > 50:
        raise HTTPException(status_code=400, detail="用户名长度应在2-50字符之间")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="密码长度至少4位")

    db = next(get_db())
    try:
        # Check if username exists
        existing = db.query(UserModel).filter(UserModel.username == username).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")

        # First user becomes admin
        user_count = db.query(UserModel).count()
        if user_count == 0:
            role = "admin"
        elif role not in ("student", "teacher", "admin"):
            role = "student"

        user = UserModel(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=hash_password(password),
            display_name=display_name or username,
            email=email,
            role=role,
        )
        db.add(user)
        db.commit()

        token = create_access_token({"sub": user.id, "role": user.role})
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "token": token,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")
    finally:
        db.close()


@app.post("/api/auth/login")
async def login(request: dict):
    """用户登录"""
    username = request.get("username", "").strip()
    password = request.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    db = next(get_db())
    try:
        user = db.query(UserModel).filter(
            UserModel.username == username, UserModel.is_active == True
        ).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        token = create_access_token({"sub": user.id, "role": user.role})
        return {
            "token": token,
            "user": user.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")
    finally:
        db.close()


@app.get("/api/auth/me")
async def get_me(user=Depends(require_auth)):
    """获取当前用户信息"""
    return user.to_dict()


@app.put("/api/auth/profile")
async def update_profile(request: dict, user=Depends(require_auth)):
    """更新用户资料"""
    db = next(get_db())
    try:
        if request.get("display_name"):
            user.display_name = request["display_name"]
        if "email" in request:
            user.email = request["email"]
        if request.get("avatar_url"):
            user.avatar_url = request["avatar_url"]
        db.commit()
        return {"status": "updated", "user": user.to_dict()}
    finally:
        db.close()


@app.put("/api/auth/password")
async def change_password(request: dict, user=Depends(require_auth)):
    """修改密码"""
    current = request.get("current_password", "")
    new = request.get("new_password", "")
    if not current or not new:
        raise HTTPException(status_code=400, detail="请输入当前密码和新密码")
    if len(new) < 4:
        raise HTTPException(status_code=400, detail="新密码长度至少4位")

    db = next(get_db())
    try:
        db_user = db.query(UserModel).filter(UserModel.id == user.id).first()
        if not verify_password(current, db_user.password_hash):
            raise HTTPException(status_code=400, detail="当前密码错误")
        db_user.password_hash = hash_password(new)
        db.commit()
        return {"status": "updated"}
    finally:
        db.close()


@app.get("/api/auth/users")
async def list_users(user=Depends(require_role(["admin"]))):
    """获取用户列表（仅管理员）"""
    db = next(get_db())
    try:
        users = db.query(UserModel).order_by(UserModel.created_at.desc()).all()
        return {"users": [u.to_dict() for u in users]}
    finally:
        db.close()


@app.put("/api/auth/users/{user_id}")
async def update_user(user_id: str, request: dict, user=Depends(require_role(["admin"]))):
    """更新用户信息（仅管理员）"""
    db = next(get_db())
    try:
        target = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="用户不存在")
        if "role" in request and request["role"] in ("student", "teacher", "admin"):
            target.role = request["role"]
        if "is_active" in request:
            target.is_active = bool(request["is_active"])
        db.commit()
        return {"status": "updated", "user": target.to_dict()}
    except HTTPException:
        raise
    finally:
        db.close()


# ==================== 学习进度端点 ====================

@app.get("/api/progress/dashboard")
async def get_progress_dashboard(user=Depends(require_auth)):
    """获取学习进度仪表板"""
    db = next(get_db())
    try:
        svc = ProgressService(db)
        return JSONResponse(content=svc.get_user_dashboard(user.id), media_type="application/json; charset=utf-8")
    finally:
        db.close()


@app.get("/api/progress/document/{doc_id}")
async def get_document_progress(doc_id: str, user=Depends(require_auth)):
    """获取特定文档的学习进度"""
    db = next(get_db())
    try:
        svc = ProgressService(db)
        return svc.get_document_progress(user.id, doc_id)
    finally:
        db.close()


@app.post("/api/progress/reading")
async def update_reading_progress(request: dict, user=Depends(require_auth)):
    """更新阅读进度"""
    doc_id = request.get("document_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="document_id不能为空")
    chunk_index = request.get("chunk_index", 0)
    time_seconds = request.get("time_seconds", 0)

    db = next(get_db())
    try:
        svc = ProgressService(db)
        p = svc.update_reading_progress(user.id, doc_id, chunk_index, time_seconds)
        return {"progress_percent": p.progress_percent, "status": p.status}
    finally:
        db.close()


@app.post("/api/progress/mastery")
async def update_mastery(request: dict, user=Depends(require_auth)):
    """更新知识点掌握度"""
    doc_id = request.get("document_id")
    point_text = request.get("knowledge_point_text")
    if not doc_id or not point_text:
        raise HTTPException(status_code=400, detail="document_id和knowledge_point_text不能为空")
    delta = request.get("delta", 0.1)

    db = next(get_db())
    try:
        svc = ProgressService(db)
        m = svc.update_knowledge_mastery(user.id, doc_id, point_text, delta)
        return {"mastery_level": m.mastery_level, "review_count": m.review_count}
    finally:
        db.close()


@app.post("/api/progress/session/start")
async def start_study_session(request: dict, user=Depends(require_auth)):
    """开始学习会话"""
    doc_id = request.get("document_id")
    session_type = request.get("session_type", "reading")

    db = next(get_db())
    try:
        svc = ProgressService(db)
        s = svc.start_study_session(user.id, doc_id, session_type)
        return {"session_id": s.id}
    finally:
        db.close()


@app.post("/api/progress/session/end")
async def end_study_session(request: dict, user=Depends(require_auth)):
    """结束学习会话"""
    session_id = request.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id不能为空")

    db = next(get_db())
    try:
        svc = ProgressService(db)
        s = svc.end_study_session(session_id)
        if not s:
            raise HTTPException(status_code=404, detail="会话不存在")
        return {"duration_seconds": s.duration_seconds}
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)