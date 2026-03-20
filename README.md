# 武汉外国语学校 - 智能学习平台

这是一个基于AI的智能学习平台，为武汉外国语学校设计，包含智能导学和知识库管理功能。

## 技术架构

- **前端**: Vue.js 3 + TypeScript + Element Plus
- **后端**: Python FastAPI + LangChain + ChromaDB
- **AI模型**: 支持本地部署和第三方API集成

## 主要功能

### AI智能导学平台
- 🗨️ **智能聊天**: 与AI助手进行学习对话
- 🔍 **知识检索**: 快速查找相关知识
- 📚 **知识交互**: 知识点学习和互动

### 智能学习系统
- 📁 **文档上传**: 支持多种格式的教学资料上传
- 📊 **知识结构化**: 自动构建知识结构
- 📋 **知识库管理**: 教学知识库的增删改查

## 文件夹结构

```
ailearning/
├── frontend/           # 前端代码
│   ├── src/           # Vue应用源码
│   │   ├── pages/     # 页面组件
│   │   ├── views/     # 布局和公共组件
│   │   └── router/    # 路由配置
├── backend/           # 后端代码
│   ├── api/           # API端点
│   ├── models/        # 数据模型
│   └── services/      # 业务逻辑
└── data/             # 数据存储
    └── knowledge_base/ # 知识库数据
```

## 环境要求

### 前端
- Node.js 18+
- npm 或 pnpm

### 后端
- Python 3.8+
- Redis (推荐)

## 安装和运行
安装olloma
irm https://ollama.com/install.ps1 | iex
<!-- 下载大模型 -->
ollama run qwen2.5
### 1. 安装前端依赖
```bash
cd frontend
npm install
```

### 2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动后端服务
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端开发服务器
```bash
cd frontend
npm run dev
```

## 开发计划

### 已完成
- [x] 项目架构设计
- [x] 前端界面框架
- [x] 后端API基础
- [x] 聊天功能
- [x] 知识库管理界面
- [x] 文档上传功能

### 计划中
- [ ] AI模型集成（本地和云服务）
- [ ] 知识结构化处理
- [ ] 向量检索优化
- [ ] 用户权限管理
- [ ] 性能优化

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

MIT License

## 联系方式

- 项目名称：武汉外国语学校智能学习平台
- 联系邮箱：ai@whfls.edu.cn
- 版本：1.0.0