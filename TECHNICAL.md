# 邮件检索问答系统 — 技术文档

## 1. 项目概述

本项目是一个基于 RAG（Retrieval-Augmented Generation）架构的邮件智能检索问答系统，面向金融信托公司内部使用。系统能够对 100 封历史邮件（含 90+ 个附件）进行语义检索，用户通过自然语言提问，系统自动检索相关邮件并生成回答，同时展示来源引用。

**核心价值**：将分散在大量邮件和附件中的业务信息（信托计划、基金净值、合规报告、风控数据等）转化为可即时查询的知识库。

---

## 2. 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **前端框架** | React | 19.x | UI 组件化开发 |
| **前端语言** | TypeScript | 5.9 | 类型安全 |
| **CSS 框架** | Tailwind CSS | 4.x | 原子化样式 |
| **构建工具** | Vite | 8.x | 开发服务器 + 构建 |
| **前端测试** | Vitest + Testing Library | 4.x | 组件测试 |
| **后端框架** | FastAPI | 0.115 | 异步 API 服务 |
| **后端语言** | Python | 3.12 | 后端开发 |
| **向量数据库** | ChromaDB | 0.5 | 邮件内容向量化存储与检索 |
| **元数据存储** | SQLite (aiosqlite) | - | 对话历史、Memory 持久化 |
| **LLM** | MiniMax M2.7 | - | 答案生成、对话标题生成、查询改写 |
| **文件解析** | PyPDF2, python-docx, openpyxl, python-pptx | - | 附件内容提取 |
| **PDF 生成** | reportlab | 4.x | 假数据 PDF 附件生成 |
| **图片处理** | Pillow | 11.x | 假数据图片附件生成 |

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (React + Vite)                    │
│  ┌───────────┐  ┌─────────────────────────────────────┐  │
│  │  Sidebar   │  │           ChatArea                  │  │
│  │ 对话列表    │  │  MessageBubble (用户/助手消息)       │  │
│  │ 新建/删除   │  │  SourceCard (来源引用卡片)           │  │
│  │ 重命名      │  │  InputArea (输入框)                  │  │
│  └───────────┘  └─────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ Vite Proxy → /api
┌────────────────────────▼────────────────────────────────┐
│                  后端 (FastAPI)                           │
│                                                          │
│  ┌──────────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ conversations.py │  │   chat.py    │  │ memory.py │  │
│  │ 对话 CRUD API     │  │ 问答 API     │  │ Memory API│  │
│  └────────┬─────────┘  └──────┬───────┘  └─────┬─────┘  │
│           │                   │                │         │
│  ┌────────▼───────────────────▼────────────────▼──────┐  │
│  │                  Services Layer                     │  │
│  │  ┌─────────┐ ┌──────────┐ ┌─────┐ ┌────────────┐  │  │
│  │  │indexer  │ │retriever │ │ llm │ │  memory    │  │  │
│  │  │向量索引  │ │混合检索   │ │RAG  │ │ 偏好记录   │  │  │
│  │  └────┬────┘ └────┬─────┘ └──┬──┘ └─────┬──────┘  │  │
│  └───────┼───────────┼──────────┼───────────┼─────────┘  │
│  ┌───────▼───┐ ┌─────▼─────┐ ┌──▼──────┐ ┌─▼────────┐  │
│  │ ChromaDB  │ │ ChromaDB  │ │ MiniMax │ │ SQLite   │  │
│  │ (写入索引) │ │ (查询)    │ │  API    │ │(对话/Mem) │  │
│  └───────────┘ └───────────┘ └─────────┘ └──────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 4. 核心功能实现

### 4.1 数据层 — 假邮件生成 (`seed_data.py`)

生成 100 封金融信托场景邮件，覆盖 8 个业务线：

| 业务场景 | 数量 | 附件类型 | 内容示例 |
|---------|------|---------|---------|
| 信托业务 | 15封 | docx/pptx/xlsx | 信托设立方案、尽调报告、收益分配、清算报告 |
| 基金投资 | 15封 | xlsx/pdf/csv | 基金净值表、持仓分析、业绩归因 |
| 合规监管 | 12封 | docx/txt | 反洗钱自查、净资本报告、资管新规整改 |
| 风控报告 | 10封 | xlsx/pdf | 信用风险监测、逾期预警、压力测试 |
| 法务合同 | 12封 | pdf/docx | 信托合同、托管协议、诉讼进展 |
| 运营管理 | 12封 | docx/txt/png/jpg | 兑付通知、培训安排、系统升级 |
| 财富管理 | 10封 | pdf/xlsx | 家族信托咨询、慈善信托、资产配置 |
| 投研分析 | 14封 | pdf/docx/zip | 宏观经济研判、房地产分析、利率预测 |

附件格式覆盖：PDF、DOCX、XLSX、PPTX、CSV、TXT、PNG、JPG、ZIP 共 9 种。

### 4.2 文件解析 (`file_parser.py`)

将各种格式的附件提取为纯文本，用于后续向量化：

```python
PARSERS = {
    ".pdf": parse_pdf,      # PyPDF2 提取文本
    ".docx": parse_docx,    # python-docx 提取段落
    ".xlsx": parse_xlsx,    # openpyxl 提取表格数据
    ".pptx": parse_pptx,    # python-pptx 提取幻灯片文本
    ".csv": parse_csv,      # csv 模块读取
    ".txt": parse_txt,      # 直接读取
    ".png/.jpg": parse_image,  # 返回文件描述（无OCR）
    ".zip": parse_zip,      # 列出压缩包内容
}
```

### 4.3 向量索引 (`indexer.py`)

将邮件正文 + 附件内容合并为一段文本，存入 ChromaDB：

```
邮件索引文本 = 主题 + 发件人 + 收件人 + 日期 + 标签 + 正文 + [附件1内容] + [附件2内容]
```

- 使用 ChromaDB 默认 embedding 模型（onnx mini-lm-l6-v2）
- 100 封邮件分批插入（每批 40 条）
- 单条文档最大 8000 字符（超长截断）
- 应用启动时自动检查并建立索引

### 4.4 混合检索 (`retriever.py`)

由于默认 embedding 模型对中文语义理解有限，采用**关键词匹配 + 语义检索**双路召回策略：

```
用户查询 → 关键词提取 → 关键词检索 (ChromaDB where_document)
                      → 语义检索   (ChromaDB query)
                      → 合并去重 → 排序 → Top-K 结果
```

**关键词提取**核心逻辑：

1. **停用词过滤**：去掉"的"、"是"、"有"、"什么"等无意义词
2. **中英混合拆分**：`"CPI预测"` → `["CPI", "预测", "CPI预测"]`
3. **滑动窗口切分**：`"医疗健康专项信托计划"` → `["医疗", "健康", "专项", "信托", "计划", ...]`
4. **加权评分**：原始关键词权重 3 分，子片段权重 1 分，按总分排序

### 4.5 RAG 问答 (`llm.py`)

```
用户提问 → [查询改写] → 检索 Top-5 邮件 → 构建 Prompt → LLM 生成回答
                ↑                                            ↓
           对话历史                                    清理 <think> 标签
          (解析指代词)                                  过滤无关来源
```

**关键技术点**：

- **查询改写**：多轮对话中，检测指代词（"它"、"这个"），用 LLM 结合对话历史改写为完整查询
- **闲聊识别**：正则匹配"你好"、"hi"等问候语，跳过检索直接回复
- **think 标签清理**：MiniMax 模型会输出 `<think>` 思考过程，正则移除
- **无结果来源过滤**：当回答包含"没有找到"等短语时，不返回来源卡片

### 4.6 对话管理 (`conversations.py` + `chat.py`)

- **SQLite 存储**：conversations（对话）、messages（消息）、memories（记忆）三张表
- **对话 CRUD**：创建、列表、详情、重命名、删除
- **消息历史**：保存完整对话历史，支持多轮上下文
- **自动标题**：首次提问后，用 LLM 根据问题内容生成 ≤15 字的对话标题

### 4.7 Memory 系统 (`memory.py`)

- 自动分析对话中用户反复提及的关键词
- 提取为 Memory 条目，存入 SQLite
- 后续对话时将 Memory 注入 System Prompt，影响回答偏好
- 支持查询和删除 Memory

### 4.8 前端界面

| 组件 | 文件 | 功能 |
|------|------|------|
| `App.tsx` | 主布局 | 左侧 Sidebar + 右侧 ChatArea |
| `Sidebar.tsx` | 侧边栏 | 对话列表、新建、删除（悬浮图标）、重命名（双击） |
| `ChatArea.tsx` | 聊天区域 | 消息列表、空状态、loading 动画 |
| `MessageBubble.tsx` | 消息气泡 | 用户右对齐蓝色、助手左对齐白色 |
| `SourceCard.tsx` | 来源卡片 | 邮件主题、发件人、日期、附件下载链接 |
| `InputArea.tsx` | 输入区域 | Enter 发送、Shift+Enter 换行、自适应高度 |
| `useChat.ts` | 状态管理 | 对话/消息状态、API 调用、loading 管理 |

---

## 5. API 设计

### 5.1 对话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/conversations` | 创建新对话 |
| `GET` | `/api/conversations` | 获取对话列表（按更新时间倒序） |
| `GET` | `/api/conversations/{id}` | 获取对话详情（含消息历史） |
| `PUT` | `/api/conversations/{id}` | 重命名对话 |
| `DELETE` | `/api/conversations/{id}` | 删除对话（级联删除消息） |

### 5.2 聊天问答

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/conversations/{id}/messages` | 发送消息，返回 AI 回答 + 来源 |

**响应结构**：
```json
{
  "user_message": { "id": "...", "role": "user", "content": "..." },
  "assistant_message": {
    "id": "...",
    "role": "assistant",
    "content": "回答文本",
    "sources": [
      {
        "email_id": "email_001",
        "subject": "邮件主题",
        "from_": "发件人",
        "date": "2024-01-01",
        "attachments": ["report.xlsx"],
        "snippet": "邮件内容摘要..."
      }
    ]
  }
}
```

### 5.3 Memory

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/memory` | 获取所有 Memory 条目 |
| `DELETE` | `/api/memory/{id}` | 删除指定 Memory |

### 5.4 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/attachments/{filename}` | 附件文件下载（静态文件服务） |

---

## 6. 数据库设计

### SQLite Schema

```sql
-- 对话表
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 消息表
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources TEXT,  -- JSON 数组
    created_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- 记忆表
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    source_conversation_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);
```

### ChromaDB Collection

- Collection 名称：`emails`
- 距离度量：cosine
- 文档数量：100
- Metadata 字段：email_id, subject, from_name, from_email, date, tags, attachments

---

## 7. 测试体系

### 测试统计

| 模块 | 测试文件 | 用例数 | 覆盖内容 |
|------|---------|--------|---------|
| 数据层 | `test_data_layer.py` | 14 | 邮件完整性、附件存在性、格式覆盖、文件解析 |
| 检索引擎 | `test_retrieval.py` | 8 | 索引建立、正文检索、附件检索、来源完整性 |
| 对话管理 | `test_conversations.py` | 11 | CRUD、消息历史、Memory API、健康检查 |
| 前端组件 | `components.test.tsx` | 11 | 侧边栏、输入框、消息气泡、来源卡片、ChatArea |
| **总计** | **4 个测试文件** | **44** | |

### 运行命令

```bash
# 后端测试
cd backend && source .venv/bin/activate && pytest tests/ -v

# 前端测试
cd frontend && npm test
```

---

## 8. 项目结构

```
email/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口，lifespan 初始化 DB + 索引
│   │   ├── config.py               # 配置（API Key、模型、路径）
│   │   ├── database.py             # SQLite 异步连接 + Schema
│   │   ├── models/
│   │   │   ├── conversation.py     # Pydantic 模型（对话、消息、来源）
│   │   │   ├── email.py            # 邮件数据模型
│   │   │   └── memory.py           # Memory 模型
│   │   ├── routers/
│   │   │   ├── conversations.py    # 对话管理 API（CRUD）
│   │   │   ├── chat.py             # 聊天 API（RAG 问答 + 自动标题）
│   │   │   └── memory.py           # Memory API
│   │   ├── services/
│   │   │   ├── indexer.py          # ChromaDB 索引构建
│   │   │   ├── retriever.py        # 混合检索（关键词 + 语义）
│   │   │   ├── llm.py              # LLM 调用（RAG、查询改写、标题生成）
│   │   │   └── memory.py           # Memory 提取与管理
│   │   └── utils/
│   │       ├── file_parser.py      # 9 种格式附件解析
│   │       └── email_loader.py     # 邮件 JSON 加载 + 附件内容合并
│   ├── data/
│   │   ├── emails/emails.json      # 100 封邮件数据
│   │   └── attachments/            # 90+ 个附件文件
│   ├── tests/                      # 33 个后端测试
│   ├── requirements.txt            # Python 依赖
│   └── seed_data.py                # 假数据生成脚本
├── frontend/
│   └── src/
│       ├── components/             # React 组件（6 个）
│       ├── hooks/useChat.ts        # 聊天状态管理 Hook
│       ├── services/api.ts         # API 调用封装
│       └── types/index.ts          # TypeScript 类型定义
├── TECHNICAL.md                    # 本文档
├── DEMO.md                         # 演示文档
├── REQUIREMENTS.md                 # 需求文档
├── TEST.md                         # 测试指南
└── TODO.md                         # 开发任务清单
```

---

## 9. 已知限制与后续优化

| 项目 | 当前状态 | 优化方向 |
|------|---------|---------|
| Embedding 模型 | ChromaDB 默认模型（英文优先） | 切换为 MiniMax embo-01 或 OpenAI text-embedding-3-small |
| 中文分词 | 滑动窗口 + 停用词过滤 | 引入 jieba 分词提升精度 |
| 图片附件 | 仅返回文件描述 | 接入 OCR 或多模态模型 |
| 实时性 | 启动时一次性建索引 | 支持增量索引更新 |
| 并发 | 单进程 | 部署时使用 gunicorn + uvicorn workers |
| 认证 | 无 | 添加 JWT 认证 |
