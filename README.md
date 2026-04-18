# 武汉外国语学校 - 智能学习平台

基于AI的智能学习平台，集成智能导学和知识库管理功能。

## 技术架构

| 层级   | 技术栈                                        |
| ------ | --------------------------------------------- |
| 前端   | Vue.js 3 + TypeScript + Element Plus + Vite   |
| 后端   | Python FastAPI + SQLAlchemy                   |
| 数据库 | MySQL                                         |
| AI模型 | Ollama / OpenAI / Anthropic / 智谱 / 通义千问 |

## 主要功能

### AI智能导学

- 🗨️ **智能聊天**: 与AI助手进行学习对话，支持多厂商模型切换
- 🔍 **知识检索**: 快速查找相关知识内容
- 📚 **知识交互**: 知识点学习和互动

### 知识库管理

- 📁 **文档上传**: 支持 PDF、DOCX、TXT、XLSX、MD 格式
- 💾 **原始文件存储**: 自动保存原始文件到 knowledge_base 目录
- 📊 **知识结构化**: 自动提取文档文本内容
- 📋 **知识库管理**: 教学知识库的增删改查

## 项目结构

```
ailearning/
├── frontend/                    # 前端代码
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   ├── views/              # 布局和公共组件
│   │   ├── router/             # 路由配置
│   │   └── main.ts             # 入口文件
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # 后端代码
│   ├── main.py                 # FastAPI 主入口
│   ├── config.json             # 配置文件
│   ├── requirements.txt        # Python依赖
│   │
│   ├── core/                   # 核心模块
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   └── stream_handler.py   # 流式响应处理
│   │
│   ├── models/                 # 数据模型
│   │   └── document.py         # 文档模型
│   │
│   ├── services/               # 业务服务
│   │   ├── ai_service.py       # AI服务
│   │   └── document_processor.py  # 文档处理
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
└── README.md
```

## 环境要求

| 组件    | 版本要求                    |
| ------- | --------------------------- |
| Node.js | 18+                         |
| Python  | 3.8+                        |
| MySQL   | 5.7+                        |
| Ollama  | 最新版 (可选，用于本地模型) |

## 快速开始

### 1. 安装 Ollama (可选)

```powershell
# Windows PowerShell
irm https://ollama.com/install.ps1 | iex

# 下载模型
ollama pull qwen2.5
ollama run qwen2.5
```

### 2. 安装依赖

```bash
# 前端
cd frontend
npm install

# 后端
cd backend
pip install -r requirements.txt
```

### 3. 配置数据库

创建 MySQL 数据库：

```sql
CREATE DATABASE ailearning CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 `backend/core/database.py` 中的数据库连接信息。

### 4. 启动服务

```bash
# 启动后端 (端口 8000)
cd backend
python main.py
# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端 (端口 5173)
cd frontend
npm run dev
```
  - 用户名: admin                                                                                                                                                 
  - 密码: admin123 
### 5. 访问应用

- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs
- API ReDoc: http://localhost:8000/redoc

## 支持的AI厂商

| 厂商        | 是否需要API Key | 说明                |
| ----------- | --------------- | ------------------- |
| Ollama      | 否              | 本地部署，免费      |
| OpenAI      | 是              | GPT系列模型         |
| Anthropic   | 是              | Claude系列模型      |
| 智谱AI      | 是              | GLM系列模型         |
| 通义千问    | 是              | Qwen系列模型        |
| SiliconFlow | 是              | 多种开源模型        |
| 自定义      | 是              | 兼容OpenAI格式的API |

---

## 📖 后端接口文档

详细的API接口文档请查看 **[inter.md](inter.md)**

## ⚙️ 配置文件

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
- [X] 向量检索优化 (ChromaDB+语义搜索+混合检索)
- [X] 用户权限管理 (JWT认证+RBAC角色控制)
- [X] 学习进度追踪 (文档进度+知识点掌握度+学习会话)

### 计划中

(暂无)

## 许可证

MIT License

## 联系方式

- 项目名称：武汉外国语学校智能学习平台
- 版本：2.0.0
