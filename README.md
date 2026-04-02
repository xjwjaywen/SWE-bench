# 邮件检索问答系统

基于 AI 的邮件智能检索系统。通过自然语言提问，从历史邮件（含附件）中检索信息，生成回答并附上来源。

## 功能特性

- **智能问答**：自然语言提问，AI 从邮件库中检索并生成答案
- **来源引用**：每个回答附带邮件来源（主题、发件人、时间、附件）
- **多对话管理**：创建多个独立对话，随时切换、重命名、删除
- **上下文记忆**：支持多轮对话，理解上下文
- **Memory 系统**：记住用户偏好，跨对话持久化
- **附件检索**：支持 PDF、Word、Excel、PPT、CSV、TXT 等格式的附件内容检索
- **附件下载**：来源引用中可直接下载附件文件

## 技术栈

- **前端**：React 19 + TypeScript + Tailwind CSS 4 + Vite
- **后端**：Python 3.12 + FastAPI
- **向量数据库**：ChromaDB
- **LLM**：OpenAI GPT-4o
- **Embedding**：OpenAI text-embedding-3-small（开发环境使用 ChromaDB 默认 embedding）
- **元数据存储**：SQLite

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- OpenAI API Key

### 后端启动

```bash
cd backend
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

# 生成假邮件数据（100封邮件 + 90个附件）
python seed_data.py

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 环境变量

```bash
# backend/.env
OPENAI_API_KEY=your_api_key_here
```

## 运行测试

```bash
# 后端测试（33个用例）
cd backend && source .venv/bin/activate && pytest tests/ -v

# 前端测试（11个用例）
cd frontend && npm test
```

## 项目结构

```
email/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，路由注册
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # SQLite 数据库管理
│   │   ├── models/              # Pydantic 数据模型
│   │   ├── routers/             # API 路由
│   │   │   ├── chat.py          # 聊天/问答 API
│   │   │   ├── conversations.py # 对话管理 API
│   │   │   └── memory.py        # Memory API
│   │   ├── services/            # 业务逻辑
│   │   │   ├── indexer.py       # ChromaDB 邮件索引
│   │   │   ├── retriever.py     # 语义检索服务
│   │   │   ├── llm.py           # LLM 调用（RAG）
│   │   │   └── memory.py        # Memory 管理
│   │   └── utils/
│   │       ├── file_parser.py   # 附件解析（PDF/DOCX/XLSX/PPTX/CSV/TXT）
│   │       └── email_loader.py  # 邮件数据加载
│   ├── data/
│   │   ├── emails/              # 邮件 JSON 数据
│   │   └── attachments/         # 附件文件（90个）
│   ├── tests/                   # 后端测试（33个用例）
│   ├── requirements.txt
│   └── seed_data.py             # 假数据生成脚本（100封邮件）
├── frontend/
│   └── src/
│       ├── components/          # React 组件
│       │   ├── ChatArea.tsx     # 聊天区域
│       │   ├── MessageBubble.tsx # 消息气泡
│       │   ├── SourceCard.tsx   # 来源引用卡片
│       │   ├── Sidebar.tsx      # 侧边栏（对话列表）
│       │   └── InputArea.tsx    # 输入区域
│       ├── hooks/useChat.ts     # 聊天状态管理
│       ├── services/api.ts      # API 调用封装
│       └── types/index.ts       # TypeScript 类型定义
├── REQUIREMENTS.md              # 需求文档
├── TEST.md                      # 测试指南
└── TODO.md                      # 开发任务清单
```

## API 文档

启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 文档。

## 文档

- [需求文档](REQUIREMENTS.md) — 完整功能需求和技术设计
- [测试指南](TEST.md) — 测试用例和运行方法
- [开发任务](TODO.md) — 开发进度追踪
