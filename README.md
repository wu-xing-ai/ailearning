# 武汉外国语学校 - 智能学习平台

基于AI的智能学习平台，集成智能导学和知识库管理功能。

## 技术架构

| 层级   | 技术栈                                        |
| ------ | --------------------------------------------- |
| 前端   | Vue.js 3 + TypeScript + Element Plus + Vite   |
| 后端   | Python FastAPI + SQLAlchemy                   |
| 数据库 | MySQL                                         |
| AI模型 | SiliconFlow / OpenAI / Anthropic / 智谱 / 通义千问 |
| 向量搜索 | SiliconFlow Embedding API (BAAI/bge-large-zh-v1.5) |

## 主要功能

### AI智能导学

- **智能聊天**: 与AI助手进行学习对话，支持多厂商模型切换（MiniMax-M2.5、GLM-5等）
- **智能检索**: 支持关键词搜索、语义搜索、混合搜索三种模式
- **知识交互**: 知识点学习和互动
- **学习进度**: 文档学习进度追踪、知识点掌握度分析

### 知识库管理

- **文档上传**: 支持 PDF、DOCX、TXT、XLSX、MD 格式
- **原始文件存储**: 自动保存原始文件到 knowledge_base 目录
- **知识结构化**: 自动提取文档文本内容，AI增强+规则双模式处理
- **智能索引**: 文档自动分块并通过API生成向量索引，支持语义检索
- **知识库管理**: 教学知识库的增删改查

## 项目结构

```
ailearning/
├── frontend/                    # 前端代码
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   │   ├── AI-Teaching/    # AI导学相关页面
│   │   │   │   ├── Search.vue  # 智能检索
│   │   │   │   └── ...
│   │   │   ├── SmartUpload.vue # 智能学习
│   │   │   ├── Knowledge.vue   # 知识交互
│   │   │   └── Settings.vue    # 系统设置
│   │   ├── views/              # 布局和公共组件
│   │   ├── router/             # 路由配置
│   │   └── main.ts             # 入口文件
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.ts
│
├── backend/                     # 后端代码
│   ├── main.py                 # FastAPI 主入口
│   ├── config.json             # 配置文件（API密钥、模型配置）
│   ├── requirements.txt        # Python依赖
│   ├── Dockerfile              # 多阶段构建，轻量化部署
│   │
│   ├── core/                   # 核心模块
│   │   ├── app_config.py       # 统一配置加载器
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   └── stream_handler.py   # 流式响应处理
│   │
│   ├── models/                 # 数据模型
│   │   ├── document.py         # 文档模型
│   │   ├── document_chunk.py   # 文档分块模型
│   │   ├── embedding.py        # 向量存储模型
│   │   ├── user.py             # 用户模型
│   │   ├── chat_session.py     # 聊天会话模型
│   │   └── learning_progress.py # 学习进度模型
│   │
│   ├── services/               # 业务服务
│   │   ├── ai_service.py       # AI服务
│   │   ├── embedding_service.py # 向量嵌入服务（API调用，无本地模型）
│   │   ├── hybrid_search.py    # 混合检索服务
│   │   └── document_processor.py # 文档处理
│   │
│   ├── ai_services/            # AI厂商服务
│   │   ├── base.py             # 基类
│   │   ├── factory.py          # 服务工厂
│   │   ├── openai_service.py
│   │   ├── anthropic_service.py
│   │   ├── zhipu_service.py
│   │   ├── qwen_service.py
│   │   ├── siliconflow_service.py
│   │   └── custom_service.py   # 自定义API服务
│   │
│   └── knowledge_base/         # 原始文件存储目录
│       └── {doc_id}/           # 按文档ID分目录
│           └── {filename}      # 原始文件
│
└── docker-compose.yml          # Docker编排配置
```

## 环境要求

| 组件    | 版本要求                    |
| ------- | --------------------------- |
| Node.js | 18+                         |
| Python  | 3.10+                       |
| MySQL   | 5.7+                        |
| Docker  | 20+（可选，用于容器化部署） |

## 快速开始

### 方式一：本地开发

#### 1. 安装依赖

```bash
# 前端
cd frontend
npm install

# 后端
cd backend
pip install -r requirements.txt
```

#### 2. 配置数据库

创建 MySQL 数据库：

```sql
CREATE DATABASE ailearning CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 `backend/core/database.py` 中的数据库连接信息。

#### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的密钥：

```bash
cd backend
cp .env.example .env
```

编辑 `backend/.env`：

```bash
# API Keys
SILICONFLOW_API_KEY=你的SiliconFlow API Key
MODELSCOPE_API_KEY=你的ModelScope API Key

# VL Extractor（视觉模型PDF提取，使用SiliconFlow）
VL_API_KEY=你的SiliconFlow API Key

# Embedding（向量嵌入）
EMBEDDING_API_KEY=你的SiliconFlow API Key

# 数据库
DATABASE_URL=mysql+pymysql://root:密码@localhost:3306/ailearning?charset=utf8mb4

# JWT密钥（生产环境务必更换）
JWT_SECRET_KEY=change-this-to-a-random-string
```

> `config.json` 中的 `api_keys`、`vl_extractor`、`embedding`、`database`、`jwt` 字段会作为 `.env` 未配置时的默认值。

#### 4. 启动服务

```bash
# 启动后端 (端口 8000)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端 (端口 5173)
cd frontend
npm run dev
```

### 方式二：Docker 部署

```bash
# 一键启动所有服务
docker-compose up -d --build
```

启动后访问：
- 前端界面: http://localhost
- 后端API: http://localhost:8000

#### 登录信息

- 用户名: admin
- 密码: admin123

### 访问应用

- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs
- API ReDoc: http://localhost:8000/redoc

## 支持的AI厂商

| 厂商        | 是否需要API Key | 说明                |
| ----------- | --------------- | ------------------- |
| SiliconFlow | 是              | 多种开源模型，免费额度 |
| OpenAI      | 是              | GPT系列模型         |
| Anthropic   | 是              | Claude系列模型      |
| 智谱AI      | 是              | GLM系列模型         |
| 通义千问    | 是              | Qwen系列模型        |
| 自定义      | 是              | 兼容OpenAI格式的API |

## 向量搜索说明

语义搜索通过API实现，无需本地部署模型：

- **Embedding模型**: `BAAI/bge-large-zh-v1.5`（通过 SiliconFlow API 调用）
- **向量存储**: MySQL数据库（`embedding_vectors` 表）
- **搜索模式**: 关键词搜索（默认）、语义搜索、混合搜索（RRF融合）

---

## 后端接口文档

详细的API接口文档请查看 **[inter.md](inter.md)**

## 配置文件

API密钥等配置存储在 **[backend/config.json](backend/config.json)**

> ⚠️ 请勿将包含真实API密钥的 config.json 提交到版本控制系统

## 开发进度

### 已完成

- [X] 项目架构设计
- [X] 前端界面框架
- [X] 后端API基础
- [X] 多厂商AI模型集成
- [X] 聊天功能 (支持流式响应)
- [X] 知识库管理界面
- [X] 文档上传功能
- [X] 原始文件存储
- [X] 自定义API模型接入
- [X] API错误处理优化
- [X] 知识结构化处理 (AI增强+规则双模式)
- [X] 语义搜索 (API向量嵌入 + MySQL向量存储)
- [X] 混合检索 (关键词+语义 RRF融合)
- [X] 用户权限管理 (JWT认证+RBAC角色控制)
- [X] 学习进度追踪 (文档进度+知识点掌握度+学习会话)
- [X] Docker容器化部署 (多阶段构建，轻量化)
- [X] 默认关键词搜索模式
- [X] PDF文档预览 (知识交互界面显示PDF第一页)

### 计划中

(暂无)

## 许可证

MIT License

## 联系方式

- 项目名称：武汉外国语学校智能学习平台
- 版本：2.0.0
