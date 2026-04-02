# 开发任务清单

## M1 — 数据层

- [x] 初始化后端项目结构 (FastAPI + requirements.txt)
- [x] 编写假邮件数据生成脚本 `seed_data.py`
  - [x] 定义邮件 JSON 结构
  - [x] 生成 100 封邮件，覆盖 8 个业务场景
  - [x] 生成各格式附件文件 (pdf/docx/xlsx/pptx/txt/csv/png/jpg/zip)
  - [x] 确保附件有实际可解析内容
- [x] 编写文件解析工具 `file_parser.py`
  - [x] PDF 解析
  - [x] DOCX 解析
  - [x] XLSX 解析
  - [x] PPTX 解析
  - [x] CSV 解析
  - [x] TXT 解析
- [x] 编写数据层测试 (D-01 ~ D-04, P-01 ~ P-06)

## M2 — 检索引擎

- [x] 编写邮件数据加载器 `email_loader.py`
- [x] 编写索引服务 `indexer.py`
  - [x] 邮件正文/主题 Embedding
  - [x] 附件内容 Embedding
  - [x] 存入 ChromaDB
- [x] 编写检索服务 `retriever.py`
  - [x] 语义检索，返回 Top-K 相关邮件
  - [x] 结果包含来源信息
- [x] 编写 LLM 服务 `llm.py`
  - [x] 构建 RAG prompt
  - [x] 调用 OpenAI 生成答案
  - [x] 解析并返回带来源的回答
- [x] 编写检索测试 (R-01 ~ R-04)

## M3 — 对话管理

- [x] 设计 SQLite 数据库 schema (对话、消息、Memory)
- [x] 编写数据模型 (email.py, conversation.py, memory.py)
- [x] 编写对话管理 API (conversations.py router)
  - [x] CRUD 对话
  - [x] 消息历史查询
- [x] 编写聊天 API (chat.py router)
  - [x] 接收用户消息
  - [x] 调用检索+LLM
  - [x] 上下文拼接（多轮对话）
  - [x] 返回答案+来源
- [x] 编写 Memory 服务和 API
  - [x] 自动从对话中提取 Memory
  - [x] Memory 查询和删除
  - [x] Memory 融入检索流程
- [x] 编写对话管理测试 (C-01 ~ C-07, M-01 ~ M-04)

## M4 — 前端界面

- [x] 初始化前端项目 (React + TypeScript + Tailwind)
- [x] 编写 API 服务层 (services/api.ts)
- [x] 编写类型定义 (types/)
- [x] 编写侧边栏组件 (Sidebar.tsx)
  - [x] 对话列表
  - [x] 新建对话按钮
  - [x] 对话右键菜单（重命名、删除）
- [x] 编写聊天区域组件 (ChatArea.tsx)
  - [x] 消息气泡 (MessageBubble.tsx)
  - [x] 来源引用卡片 (SourceCard.tsx)
  - [x] 附件预览
- [x] 编写输入区域组件 (InputArea.tsx)
  - [x] Enter 发送 / Shift+Enter 换行
  - [x] Loading 状态
- [x] 整合 App.tsx 布局
- [x] 响应式设计适配
- [x] 编写前端测试 (F-01 ~ F-06)

## M5 — 集成测试与文档

- [x] 端到端测试 (E-01 ~ E-03)
- [x] 更新 README.md（最终版）
- [x] 更新 CLAUDE.md（架构信息）
- [x] 更新 TEST.md（补充遗漏用例）
- [x] 编写 PROGRESS.md（经验总结）
