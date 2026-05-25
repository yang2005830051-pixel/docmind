# DocMind - 技术文档智能问答系统

基于 RAG（检索增强生成）的智能文档问答系统，支持多种文档格式，采用混合分块、分层检索和重排序技术，提供精准的技术文档问答能力。

## 功能特点

- **混合分块算法**：自动识别代码块、Markdown 表格、普通文本，分别采用最优分块策略
- **分层检索**：摘要检索 → 内容检索 → BGE-Reranker 重排序，三层过滤确保结果精准
- **多格式支持**：PDF、TXT、Markdown 文档直接上传
- **多轮对话**：支持上下文记忆，基于 SQLite 持久化存储
- **多模型切换**：支持 OpenAI Embedding + DeepSeek LLM
- **简洁 UI**：Streamlit 构建，API Key 在线配置

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Streamlit |
| 向量数据库 | ChromaDB |
| Embedding | OpenAI text-embedding-3-small |
| LLM | DeepSeek-Chat |
| 重排序 | BGE-Reranker (BAAI/bge-reranker-base) |
| 对话管理 | LangChain + LangGraph |
| 持久化 | SQLite |

## 快速开始

### 环境要求

- Windows 10/11
- Python 3.12

### 安装运行

```bash
# 首次安装（自动创建虚拟环境、安装依赖）
双击 首次安装.bat

# 启动应用
双击 启动.bat
```

浏览器自动打开 `http://localhost:8501`，首次进入会弹出 API Key 配置窗口。

### Docker 部署

```bash
# 安装 Docker Desktop 后
双击 Docker启动.bat

# 或手动执行
docker compose up -d
```

## API Key 配置

首次启动时会弹出配置窗口，填入**任意一个**可用的 Key 即可：

| Key | 用途 | 获取地址 |
|-----|------|----------|
| OpenAI API Key | 文档向量化（Embedding） | https://platform.openai.com/api-keys |
| DeepSeek API Key | AI 对话（LLM） | https://platform.deepseek.com/api_keys |

更换 Key：点击页面右上角 🔑 图标。

## 项目结构

```
├── app.py                  # Streamlit 主应用
├── config.py               # 配置管理
├── requirements.txt        # 依赖列表
├── .env.example            # 环境变量模板
├── Dockerfile
├── docker-compose.yml
├── src/
│   ├── __init__.py
│   ├── chunker.py          # 混合分块算法
│   ├── embeddings.py       # OpenAI Embedding
│   ├── vector_store.py     # ChromaDB 向量存储
│   ├── retriever.py        # 分层检索
│   ├── reranker.py         # BGE-Reranker 重排序
│   ├── llm.py              # DeepSeek LLM
│   ├── memory.py           # 对话记忆（SQLite）
│   ├── rag_chain.py        # RAG 链编排
│   ├── document_loader.py  # 文档加载与处理
│   └── logger.py           # 日志系统
└── tests/                  # 单元测试
```

## 测试

```bash
.venv/Scripts/pytest tests/ -v
```

## License

MIT
