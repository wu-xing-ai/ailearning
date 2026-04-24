# AI教学助手 - 后端接口文档

基础URL: `http://localhost:8000`

---

## 目录

- [健康检查](#健康检查)
- [文档管理](#文档管理)
- [AI聊天接口](#ai聊天接口)
- [AI配置管理](#ai配置管理)
- [聊天会话管理](#聊天会话管理)
- [知识库处理](#知识库处理)
- [错误响应](#错误响应)
- [配置文件说明](#配置文件说明)

---

## 健康检查

### 检查服务状态

```
GET /api/health
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-21T12:00:00.000000"
}
```

---

## 文档管理

### 上传文档

```
POST /api/documents
Content-Type: multipart/form-data
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 文档文件 (PDF/DOCX/TXT/XLSX/MD) |

**响应示例:**
```json
{
  "id": "uuid-string",
  "status": "uploaded",
  "filename": "document.pdf",
  "file_type": "PDF",
  "file_path": "/path/to/knowledge_base/{id}/document.pdf"
}
```

---

### 获取文档列表

```
GET /api/documents
```

**响应示例:**
```json
[
  {
    "id": "uuid-string",
    "filename": "document.pdf",
    "file_type": "PDF",
    "content": "提取的文本内容...",
    "processed": false,
    "created_at": "2026-03-21T12:00:00"
  }
]
```

---

### 搜索文档

```
GET /api/documents/search?q=关键词
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |

**响应示例:**
```json
[
  {
    "id": "uuid-string",
    "filename": "document.pdf",
    "file_type": "PDF",
    "snippet": "...关键词相关内容...",
    "processed": false,
    "created_at": "2026-03-21T12:00:00"
  }
]
```

---

### 删除文档

```
DELETE /api/documents/{doc_id}
```

**响应示例:**
```json
{
  "status": "deleted",
  "id": "uuid-string"
}
```

---

## AI聊天接口

### 与AI对话

```
POST /api/ai/chat
Content-Type: application/json
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 用户输入的提示 |
| stream | boolean | 否 | 是否流式响应，默认false |
| modelConfig | object | 否 | 模型配置 |

**modelConfig 结构:**
```json
{
  "type": "custom",        // 厂商类型: ollama/openai/anthropic/zhipu/qwen/siliconflow/custom
  "name": "glm-5",         // 模型名称
  "apiKey": "sk-xxx",      // API密钥 (自定义厂商必填)
  "apiUrl": "https://..."  // API地址 (自定义厂商必填)
}
```

**非流式响应示例:**
```json
{
  "response": "AI回复的内容...",
  "model": "glm-5",
  "provider": "custom",
  "timestamp": "2026-03-21T12:00:00.000000"
}
```

**流式响应格式 (SSE):**
```
data: {"content": "AI"}
data: {"content": "回复"}
data: {"content": "的内容"}
data: {"done": true}
```

---

## AI配置管理

### 获取AI配置

```
GET /api/ai/config
```

**响应示例:**
```json
{
  "model": "qwen2.5",
  "base_url": "http://localhost:11434",
  "provider": "ollama",
  "supported_providers": ["ollama", "openai", "anthropic", "zhipu", "qwen", "siliconflow", "custom"]
}
```

---

### 更新AI配置

```
PUT /api/ai/config
Content-Type: application/json
```

**请求参数:**
```json
{
  "model": "qwen2.5",
  "base_url": "http://localhost:11434",
  "apiKeys": {
    "openai": "sk-xxx",
    "anthropic": "sk-xxx"
  }
}
```

---

### 获取支持的厂商列表

```
GET /api/ai/providers
```

**响应示例:**
```json
{
  "providers": ["ollama", "openai", "anthropic", "zhipu", "qwen", "siliconflow", "custom"],
  "info": {
    "ollama": {
      "name": "Ollama本地模型",
      "requires_api_key": false,
      "default_models": ["llama3.2", "qwen2"]
    },
    "openai": {
      "name": "OpenAI (GPT)",
      "requires_api_key": true,
      "default_models": ["gpt-4", "gpt-3.5-turbo"]
    },
    "custom": {
      "name": "自定义API",
      "requires_api_key": true,
      "default_models": []
    }
  }
}
```

---

### 设置厂商API密钥

```
POST /api/ai/api-keys
Content-Type: application/json
```

**请求参数:**
```json
{
  "provider": "openai",
  "apiKey": "sk-xxx"
}
```

**响应示例:**
```json
{
  "status": "success",
  "provider": "openai"
}
```

---

### 删除厂商API密钥

```
DELETE /api/ai/api-keys/{provider}
```

**响应示例:**
```json
{
  "status": "deleted",
  "provider": "openai"
}
```

---

### 获取可用模型列表

```
GET /api/ai/models
```

**响应示例:**
```json
{
  "models": ["llama3.2", "qwen2.5", "mistral"],
  "current": "qwen2.5",
  "provider": "ollama"
}
```

---

### 重置对话上下文

```
POST /api/ai/reset
```

**响应示例:**
```json
{
  "status": "reset",
  "message": "对话上下文已重置"
}
```

---

## 聊天会话管理

### 创建聊天会话

```
POST /api/chat/session
```

**响应示例:**
```json
{
  "id": "uuid-string",
  "title": "会话 1"
}
```

---

### 添加消息到会话

```
POST /api/chat/{session_id}/messages
Content-Type: application/json
```

**请求参数:**
```json
{
  "role": "user",
  "content": "消息内容"
}
```

**role 可选值:** `user` | `assistant` | `system`

---

### 获取会话消息列表

```
GET /api/chat/{session_id}/messages
```

**响应示例:**
```json
[
  {
    "role": "user",
    "content": "你好",
    "timestamp": "2026-03-21T12:00:00"
  },
  {
    "role": "assistant",
    "content": "你好！有什么可以帮助你的吗？",
    "timestamp": "2026-03-21T12:00:01"
  }
]
```

---

## 知识库处理

### 处理知识库文档

```
POST /api/knowledge/process?doc_id={doc_id}
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| doc_id | string | 是 | 文档ID |

**响应示例:**
```json
{
  "status": "processed",
  "document_id": "uuid-string"
}
```

---

### 获取文档预览

```
GET /api/preview?doc_id={doc_id}
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| doc_id | string | 是 | 文档ID |

**响应:** 成功时返回 PNG 图片二进制数据

```
Content-Type: image/png
```

**错误响应:**

| 状态码 | 说明 |
|--------|------|
| 404 | 文档不存在 或 非PDF无预览 |
| 500 | 预览生成失败 |

---

## 错误响应

所有接口在出错时返回统一格式：

```json
{
  "detail": "错误描述信息"
}
```

**常见HTTP状态码:**

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 配置文件说明

API密钥存储在 `backend/config.json`:

```json
{
  "provider": "ollama",
  "model": "qwen2.5",
  "base_url": "http://localhost:11434",
  "api_keys": {
    "openai": "",
    "anthropic": "",
    "zhipu": "",
    "qwen": "",
    "siliconflow": "",
    "custom": ""
  },
  "custom_models": [
    {
      "name": "模型名称",
      "provider": "siliconflow",
      "api_url": "https://api.example.com/v1",
      "api_key": ""
    }
  ]
}
```

> ⚠️ **安全提示**: 请勿将包含真实API密钥的 config.json 提交到版本控制系统。
