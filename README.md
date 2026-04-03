# 笔记本智能问答助手 - RAG 智能体系统

基于 **RAG (Retrieval-Augmented Generation)** 和 **Agent** 技术的笔记本电脑智能客服系统，提供专业、精准的笔记本电脑咨询、故障诊断、选购推荐等服务。

## 📋 目录

- [项目简介](#项目简介)
- [技术栈](#技术栈)
- [核心功能](#核心功能)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [API 接口](#api 接口)
- [开发指南](#开发指南)

---

## 项目简介

本项目是一个智能化的笔记本电脑客服系统，结合了以下核心技术：

- **RAG (检索增强生成)**: 从专业知识库中检索相关信息，生成准确的回答
- **Agent (智能体)**: 具备自主决策能力，能够处理复杂的多轮对话任务
- **前后端分离**: React 前端 + FastAPI 后端，支持高并发和灵活部署

### 应用场景

- ✅ 笔记本电脑使用技巧咨询
- ✅ 故障诊断与排除指导
- ✅ 硬件配置与性能分析
- ✅ 产品选购对比推荐
- ✅ 驱动安装与软件问题
- ✅ 维护保养知识科普

---

## 技术栈

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **FastAPI** | >=0.104.0 | 高性能异步 Web 框架 |
| **LangChain** | >=0.1.0 | LLM 应用开发框架 |
| **ChromaDB** | >=0.4.0 | 向量数据库 |
| **Dashscope** | >=1.14.0 | 通义千问大模型 SDK |
| **PyYAML** | >=6.0.1 | 配置文件解析 |
| **Python-multipart** | >=0.0.6 | 文件上传支持 |

### 文档处理

| 库 | 用途 |
|----|------|
| **PyPDF2** | PDF 文档解析 |
| **python-docx** | Word 文档解析 |
| **unstructured** | 非结构化数据处理 |
| **markdown** | Markdown 文件解析 |

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **React** | ^18.2.0 | 前端 UI 框架 |
| **TypeScript** | ^5.2.2 | 类型安全的 JavaScript |
| **Vite** | ^5.0.0 | 现代化构建工具 |
| **Axios** | ^1.6.0 | HTTP 客户端 |

---

## 核心功能

### 1. 智能问答 (Chat)
- 基于自然语言的交互式问答
- 支持上下文理解的多轮对话
- 自动检索相关知识库生成答案

### 2. 文档管理 (File)
- 支持多种格式文档上传（PDF、Word、TXT、Markdown）
- 自动文本分块与向量化
- 增量更新向量索引

### 3. RAG 检索增强 (RAG)
- 语义相似度检索
- 多路召回策略
- 相关性排序与重排序

### 4. Agent 自主决策
- 任务规划与分解
- 工具调用与协调
- 记忆管理与上下文维护

---

## 系统架构

```
┌─────────────────┐
│   React 前端    │
│   (TypeScript)  │
└────────┬────────┘
         │ HTTP/REST API
         ▼
┌─────────────────┐
│  FastAPI 后端   │
│   (Python)      │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐
│ Agent  │ │  RAG   │ │ Embedding│ │Vector DB│
│ 模块   │ │ 模块   │ │  模块    │ │ Chroma  │
└────────┘ └────────┘ └────────┘ └─────────┘
```

### 六大核心模块

1. **Agent 模块** (`core/agent/`)
   - ReAct 模式实现
   - 工具管理器
   - 记忆管理

2. **API 模块** (`core/api/`)
   - RESTful 路由
   - 请求/响应 Schema
   - 中间件处理

3. **Embedding 模块** (`core/embedding/`)
   - 文本向量化
   - 模型管理

4. **Loader 模块** (`core/loader/`)
   - 统一文档加载
   - 多格式解析器

5. **Preprocessing 模块** (`core/preprocessing/`)
   - 文本清洗
   - 质量检查
   - 智能分块

6. **RAG 模块** (`core/rag/`)
   - 检索器
   - 生成器
   - 向量存储管理

---

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- npm 或 yarn

### 1. 安装依赖

#### 后端依赖

```bash
cd AI大模型RAG与智能体开发_Agent项目
pip install -r requirements.txt
```

#### 前端依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# Dashscope API Key
DASHSCOPE_API_KEY=your_api_key_here

# 其他配置（可选）
LOG_LEVEL=INFO
```

### 3. 启动服务

#### 启动后端服务

```bash
# 方式一：直接运行
python app/main.py

# 方式二：使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将在 `http://localhost:8000` 启动

- API 文档：`http://localhost:8000/docs`
- Redoc 文档：`http://localhost:8000/redoc`

#### 启动前端服务

```bash
cd frontend
npm run dev
```

前端服务将在 `http://localhost:5173` 启动（端口可能不同，以实际输出为准）

### 4. 访问应用

打开浏览器访问：`http://localhost:5173`

---

## 项目结构

```
AI大模型RAG与智能体开发_Agent项目/
├── app/                          # 应用层（业务逻辑）
│   ├── api/                      # API 相关
│   │   ├── database/             # 数据库连接
│   │   ├── file_routers/         # 文件路由
│   │   └── models/               # 数据模型
│   ├── core/                     # 核心配置
│   ├── service/                  # 业务服务
│   ├── utils/                    # 工具函数
│   └── main.py                   # FastAPI 入口
│
├── core/                         # 核心模块层
│   ├── agent/                    # Agent 模块
│   ├── api/                      # API 模块
│   │   ├── routes/               # API 路由
│   │   └── schemas/              # 数据 Schema
│   ├── embedding/                # 嵌入模型
│   ├── loader/                   # 文档加载
│   │   └── parsers/              # 解析器
│   ├── preprocessing/            # 文本预处理
│   └── rag/                      # RAG 模块
│       ├── generator.py          # 生成器
│       ├── retriever.py          # 检索器
│       └── vector_store.py       # 向量存储
│
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── components/           # 组件
│   │   ├── services/             # API 服务
│   │   └── types/                # TypeScript 类型
│   └── package.json
│
├── config/                       # 配置文件
│   ├── agent.yml                 # Agent 配置
│   ├── chroma.yml                # ChromaDB 配置
│   ├── prompts.yml               # Prompt 配置
│   └── rag.yml                   # RAG 配置
│
├── data/                         # 数据文件
│   ├── external/                 # 外部数据
│   ├── uploads/                  # 上传文件
│   └── *.pdf, *.txt, *.csv       # 知识库文档
│
├── prompts/                      # Prompt 模板
│   ├── main_prompt.txt
│   ├── rag_summarize.txt
│   └── report_prompt.txt
│
├── logs/                         # 日志文件
├── chroma_db/                    # ChromaDB 数据
├── requirements.txt              # Python 依赖
└── README.md                     # 项目说明
```

---

## 配置说明

### 核心配置文件

#### `config/rag.yml` - RAG 配置

```yaml
chat_model_name: qwen3-max        # 聊天模型名称
embedding_model_name: text-embedding-v4  # 嵌入模型名称
```

#### `config/agent.yml` - Agent 配置

```yaml
external_data_path: data/external/records.csv  # 外部数据路径
fault_cases_path: data/fault_cases.md          # 故障案例路径
laptop_specs_path: data/laptop_specs.csv       # 笔记本配置数据路径
```

#### `config/chroma.yml` - 向量数据库配置

```yaml
# ChromaDB 连接配置
persist_directory: ./chroma_db
```

#### `config/prompts.yml` - Prompt 配置

```yaml
# Prompt 模板路径配置
main_prompt: prompts/main_prompt.txt
```

---

## API 接口

### 健康检查

```http
GET /api/health
```

**响应示例：**
```json
{
  "success": true,
  "message": "服务运行正常",
  "data": {
    "status": "healthy"
  }
}
```

### 聊天接口

```http
POST /api/chat
Content-Type: application/json

{
  "message": "我想买一台用来办公的笔记本电脑，预算 5000-6000 元",
  "conversation_id": "optional_conversation_id"
}
```

### 文件上传

```http
POST /api/files/upload
Content-Type: multipart/form-data

file: <文件>
```

### RAG 检索

```http
POST /api/rag/query
Content-Type: application/json

{
  "query": "如何清理笔记本风扇灰尘？",
  "top_k": 3
}
```

### 完整 API 文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 开发指南

### 添加新的文档解析器

1. 在 `core/loader/parsers/` 目录下创建新的解析器
2. 继承基础解析器类
3. 实现 `parse()` 方法
4. 在 `document_loader.py` 中注册

### 自定义 Prompt 模板

1. 在 `prompts/` 目录下创建 `.txt` 文件
2. 在 `config/prompts.yml` 中配置路径
3. 使用 `PromptLoader` 加载

### 扩展 Agent 工具

1. 在 `agent/tools/` 目录下创建工具类
2. 实现工具的执行逻辑
3. 在 `ToolManager` 中注册

### 日志查看

日志文件位于 `logs/` 目录，按日期命名：
- `agent_20260402.log` - 最新日志
- 历史日志按日期归档

### 常见问题

#### Q: 如何重置向量数据库？

```bash
# 删除 chroma_db 目录
rm -rf chroma_db/*

# 重新启动服务将自动初始化
```

#### Q: 如何添加新的知识库文档？

将文档放入 `data/` 目录，然后通过文件上传接口或重启服务自动加载。

#### Q: 如何更换大模型？

修改 `config/rag.yml` 中的 `chat_model_name` 和 `embedding_model_name`。

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件至项目维护者

---

**最后更新时间**: 2026-04-03
