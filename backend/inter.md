# 后端 API 接口文档

武汉外国语学校智能学习平台后端接口说明。

**基础URL**: `http://localhost:8000`

---

## 目录

1. [系统接口](#1-系统接口)
2. [文档管理接口](#2-文档管理接口)
3. [聊天会话接口](#3-聊天会话接口)
4. [AI对话接口](#4-ai对话接口)
5. [AI配置接口](#5-ai配置接口)
6. [知识库处理接口](#6-知识库处理接口)

---

## 1. 系统接口

### 1.1 健康检查

检查服务是否正常运行。

- **URL**: `GET /api/health`
- **认证**: 无

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

## 2. 文档管理接口

### 2.1 上传文档

上传文档到知识库，支持 PDF、DOCX、TXT、XLSX、MD 格式。

- **URL**: `POST /api/documents`
- **Content-Type**: `multipart/form-data`
- **认证**: 无

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 上传的文件 |

**响应示例**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "uploaded",
  "filename": "教材.pdf",
  "file_type": "PDF",
  "file_path": "E:/study/ailearning/backend/knowledge_base/550e8400.../教材.pdf"
}
```

**错误响应**:
- `400`: 不支持的文件格式
- `500`: 文件处理失败

---

### 2.2 获取文档列表

获取所有已上传的文档列表。

- **URL**: `GET /api/documents`
- **认证**: 无

**响应示例**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "教材.pdf",
    "file_type": "PDF",
    "content": "文档内容...",
    "file_path": "E:/study/ailearning/backend/knowledge_base/.../教材.pdf",
    "processed": false,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

---

### 2.3 搜索文档

根据关键词搜索文档。

- **URL**: `GET /api/documents/search`
- **认证**: 无

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |

**响应示例**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "教材.pdf",
    "file_type": "PDF",
    "snippet": "...包含关键词的内容片段...",
    "processed": false,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

### 2.4 删除文档

删除指定文档，同时删除原始文件。

- **URL**: `DELETE /api/documents/{doc_id}`
- **认证**: 无

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| doc_id | string | 文档ID |

**响应示例**:
```json
{
  "status": "deleted",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**错误响应**:
- `404`: 文档不存在

---

## 3. 聊天会话接口

### 3.1 创建聊天会话

创建一个新的聊天会话。

- **URL**: `POST /api/chat/session`
- **认证**: 无

**响应示例**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "会话 1"
}
```

---

### 3.2 添加消息

向指定会话添加消息。

- **URL**: `POST /api/chat/{session_id}/messages`
- **Content-Type**: `application/json`
- **认证**: 无

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话ID |

**请求体**:
```json
{
  "role": "user",
  "content": "你好"
}
```

**响应示例**:
```json
{
  "status": "success"
}
```

**错误响应**:
- `404`: Session not found

---

### 3.3 获取消息列表

获取指定会话的所有消息。

- **URL**: `GET /api/chat/{session_id}/messages`
- **认证**: 无

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话ID |

**响应示例**:
```json
[
  {
    "id": "msg-001",
    "role": "user",
    "content": "你好",
    "timestamp": "2024-01-15T10:30:00"
  },
  {
    "id": "msg-002",
    "role": "assistant",
    "content": "你好！有什么可以帮助你的吗？",
    "timestamp": "2024-01-15T10:30:05"
  }
]
```

**错误响应**:
- `404`: Session not found

---

## 4. AI对话接口

### 4.1 与AI对话

与AI进行对话，支持多厂商模型和流式响应。

- **URL**: `POST /api/ai/chat`
- **Content-Type**: `application/json`
- **认证**: 无

**请求体**:
```json
{
  "prompt": "请解释一下什么是机器学习？",
  "stream": false,
  "modelConfig": {
    "type": "ollama",
    "name": "qwen2.5",
    "apiKey": "可选，部分厂商需要",
    "apiUrl": "可选，自定义API地址"
  }
}
```

**请求参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 用户输入的提示词 |
| stream | boolean | 否 | 是否使用流式响应，默认false |
| modelConfig | object | 否 | 模型配置 |
| modelConfig.type | string | 否 | 厂商类型：ollama/openai/anthropic/zhipu/qwen/custom |
| modelConfig.name | string | 否 | 模型名称 |
| modelConfig.apiKey | string | 否 | API密钥 |
| modelConfig.apiUrl | string | 否 | 自定义API地址 |

**非流式响应示例**:
```json
{
  "response": "机器学习是人工智能的一个分支...",
  "model": "qwen2.5",
  "provider": "ollama",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

**流式响应**: 返回 `text/event-stream` 格式

**错误响应**:
- `400`: prompt参数不能为空 / 请先配置API密钥
- `500`: AI服务错误

---

## 5. AI配置接口

### 5.1 获取AI配置

获取当前AI配置信息。

- **URL**: `GET /api/ai/config`
- **认证**: 无

**响应示例**:
```json
{
  "provider": "ollama",
  "model": "qwen2.5",
  "base_url": "http://localhost:11434",
  "supported_providers": ["ollama", "openai", "anthropic", "zhipu", "qwen", "custom"]
}
```

---

### 5.2 更新AI配置

更新AI配置。

- **URL**: `PUT /api/ai/config`
- **Content-Type**: `application/json`
- **认证**: 无

**请求体**:
```json
{
  "provider": "ollama",
  "model": "qwen2.5",
  "base_url": "http://localhost:11434",
  "apiKeys": {
    "openai": "sk-xxx",
    "anthropic": "sk-xxx"
  }
}
```

**响应示例**:
```json
{
  "status": "updated",
  "config": {
    "provider": "ollama",
    "model": "qwen2.5",
    "base_url": "http://localhost:11434"
  }
}
```

---

### 5.3 设置API密钥

为指定厂商设置API密钥。

- **URL**: `POST /api/ai/api-keys`
- **Content-Type**: `application/json`
- **认证**: 无

**请求体**:
```json
{
  "provider": "openai",
  "apiKey": "sk-xxxxxxxx"
}
```

**响应示例**:
```json
{
  "status": "success",
  "provider": "openai"
}
```

---

### 5.4 删除API密钥

删除指定厂商的API密钥。

- **URL**: `DELETE /api/ai/api-keys/{provider}`
- **认证**: 无

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| provider | string | 厂商名称 |

**响应示例**:
```json
{
  "status": "deleted",
  "provider": "openai"
}
```

---

### 5.5 重置对话上下文

重置AI对话的上下文记忆。

- **URL**: `POST /api/ai/reset`
- **认证**: 无

**响应示例**:
```json
{
  "status": "reset",
  "message": "对话上下文已重置"
}
```

---

### 5.6 获取可用模型列表

获取当前厂商的可用模型列表。

- **URL**: `GET /api/ai/models`
- **认证**: 无

**响应示例**:
```json
{
  "models": [
    {"value": "qwen2.5", "label": "qwen2.5"},
    {"value": "llama3.2", "label": "llama3.2"}
  ],
  "current": "qwen2.5",
  "provider": "ollama"
}
```

---

### 5.7 获取指定厂商的模型列表

获取指定厂商的可用模型列表。

- **URL**: `GET /api/ai/models/{provider}`
- **认证**: 无

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| provider | string | 厂商名称 |

**响应示例**:
```json
{
  "models": [
    {"value": "gpt-4", "label": "GPT-4"},
    {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"}
  ],
  "provider": "openai"
}
```

---

### 5.8 获取对话上下文

获取当前AI对话的上下文内容。

- **URL**: `GET /api/ai/context`
- **认证**: 无

**响应示例**:
```json
{
  "context": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！"}
  ]
}
```

---

### 5.9 重置为默认配置

将AI配置重置为默认值。

- **URL**: `POST /api/ai/config/reset`
- **认证**: 无

**响应示例**:
```json
{
  "status": "reset",
  "config": {
    "provider": "ollama",
    "model": "llama3.2",
    "base_url": "http://localhost:11434"
  }
}
```

---

### 5.10 获取支持的厂商列表

获取系统支持的所有AI厂商信息。

- **URL**: `GET /api/ai/providers`
- **认证**: 无

**响应示例**:
```json
{
  "providers": ["ollama", "openai", "anthropic", "zhipu", "qwen", "custom"],
  "info": {
    "ollama": {
      "name": "Ollama本地模型",
      "requires_api_key": false,
      "default_models": ["llama3.2", "llama3.1", "mistral", "qwen2"]
    },
    "openai": {
      "name": "OpenAI (GPT)",
      "requires_api_key": true,
      "default_models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    }
  }
}
```

---

## 6. 知识库处理接口

### 6.1 处理知识库文档

将指定文档标记为已处理状态。

- **URL**: `POST /api/knowledge/process`
- **认证**: 无

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| doc_id | string | 是 | 文档ID (Query参数) |

**响应示例**:
```json
{
  "status": "processed",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**错误响应**:
- `404`: 文档不存在

---

## 数据模型

### Document 文档模型

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 文档唯一ID (UUID) |
| filename | string | 文件名 |
| file_type | string | 文件类型 (PDF/DOCX/TXT/XLSX/MD) |
| content | text | 提取的文本内容 |
| file_path | string | 原始文件存储路径 |
| processed | boolean | 是否已处理 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### Message 消息模型

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 消息唯一ID |
| role | string | 角色 (user/assistant) |
| content | string | 消息内容 |
| timestamp | datetime | 时间戳 |

### ChatSession 会话模型

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 会话唯一ID |
| title | string | 会话标题 |
| messages | array | 消息列表 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 更新日志

### v1.0.0 (2024-01)
- 初始版本
- 支持文档上传和管理
- 支持多厂商AI对话
- 支持原始文件存储