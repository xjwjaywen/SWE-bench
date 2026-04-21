# CodeReviewer：产品级代码评审 Agent 完整项目规划

## 一、项目定位

### 一句话描述
一个连接 GitHub 的 AI 代码评审 Agent，对 Pull Request 自动生成结构化评审意见。面试官可以直接安装到自己的仓库试用。

### 为什么做这个
这个项目的目标不是展示算法创新，而是展示**你能独立把一个 agent 系统做到产品级**。

具体来说，它要证明：
1. 你能做端到端的全栈开发（后端 + 前端 + 部署）
2. 你能处理真实生产环境的工程问题（流式输出、容错、成本控制、可观测性）
3. 你能设计评测体系并用数据驱动产品迭代
4. 你写的代码质量达到开源项目标准

### 和你简历上现有项目的区别

| 维度 | 现有项目（Darwinian等） | 这个项目 |
|------|------------------------|----------|
| 架构 | LangGraph 多 Agent 编排 | 单 Agent + 工程化架构 |
| 交互 | Streamlit 演示 | GitHub App + Web Dashboard |
| 部署 | 本地运行 | 云端部署，任何人可安装使用 |
| 用户 | 只有你自己 | 面试官/开源社区 |
| 工程深度 | token管理、容错 | 全链路：webhook→处理→输出→监控→评估 |
| 评测 | 手动跑几个 case | 自动化 eval pipeline |

---

## 二、产品设计

### 2.1 核心功能

用户在 GitHub 仓库安装你的 GitHub App，之后每次打开 PR，agent 自动触发评审，在 PR 页面以 review comment 形式输出结果。

评审输出包含三层：

**PR Summary（PR 概要）**
- 一句话总结这个 PR 做了什么
- 改动涉及的模块/文件分类
- 改动规模评估（小改/中等/大重构）

**File-Level Review（文件级评审）**
- 对每个改动文件的评审意见
- 聚焦：逻辑错误、边界条件遗漏、命名不规范、缺少错误处理、性能隐患
- 不做风格/格式吹毛求疵（这些交给 linter）

**Inline Comments（行级评论）**
- 在具体代码行上留 comment，像人类 reviewer 一样
- 每条 comment 包含：问题描述 + 严重程度（critical/suggestion/nitpick）+ 修复建议

### 2.2 用户交互

```
开发者打开 PR
    │
    ▼
GitHub Webhook 触发 ──→ 你的后端接收
    │
    ▼
Agent 处理（1-3 分钟）
    │
    ▼
在 PR 页面以 Review Comment 形式输出结果
    │
    ▼
开发者可以在 Dashboard 上查看：
  - 本次评审的完整 trace
  - token 消耗和成本
  - 评审耗时
  - 历史评审记录
```

### 2.3 Dashboard（Web 前端）

一个轻量的 Web 页面，提供：
- 评审历史列表（每个 PR 的评审结果、耗时、成本）
- 单次评审的 trace 详情（每一步的输入/输出/耗时/token）
- 全局统计（累计评审数、平均耗时、平均成本、top issues 分类）
- 配置管理（评审偏好：语言、严格程度、忽略规则）

前端用 React 或 Vue 都行（你会 Vue.js），部署在 Vercel 或类似平台。

---

## 三、系统架构

### 3.1 总体架构图

```
┌──────────────┐     Webhook      ┌──────────────────────┐
│   GitHub     │ ──────────────→  │   API Server         │
│   (PR event) │                  │   (FastAPI)          │
└──────────────┘                  │                      │
                                  │  ┌─────────────────┐ │
       GitHub API ←───────────────│  │  Review Engine   │ │
       (post comments)            │  │  (Agent Core)    │ │
                                  │  └────────┬────────┘ │
                                  │           │          │
                                  │  ┌────────▼────────┐ │
                                  │  │  LLM Client     │ │
                                  │  │  (多模型支持)    │ │
                                  │  └────────┬────────┘ │
                                  │           │          │
                                  │  ┌────────▼────────┐ │
                                  │  │  Trace Logger    │ │
                                  │  │  (结构化日志)    │ │
                                  │  └─────────────────┘ │
                                  └──────────┬───────────┘
                                             │
                                  ┌──────────▼───────────┐
                                  │   Database           │
                                  │   (SQLite/PostgreSQL) │
                                  │   - 评审记录          │
                                  │   - trace 数据        │
                                  │   - 用户配置          │
                                  └──────────────────────┘
                                             │
                                  ┌──────────▼───────────┐
                                  │   Dashboard          │
                                  │   (Vue.js / React)   │
                                  └──────────────────────┘
```

### 3.2 技术栈

| 组件 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | 原生支持异步、WebSocket、自动 API 文档 |
| 任务队列 | Celery + Redis（或简化为 asyncio background tasks） | PR 评审是异步长任务，不能阻塞 webhook 响应 |
| 数据库 | SQLite（开发）→ PostgreSQL（部署） | 轻量启动，生产可切换 |
| LLM | DeepSeek / Claude Sonnet（可配置） | 支持多模型切换，对比成本效果 |
| 前端 | Vue.js + TailwindCSS | 你已有 Vue 经验 |
| 部署 | Railway / Fly.io / 自建 VPS | 便宜、支持容器部署 |
| GitHub 集成 | PyGithub + GitHub App API | 官方推荐的集成方式 |

### 3.3 为什么不用 LangGraph / LangChain

和上一个项目规划里的理由一样，这里不用任何 agent 框架。原因：
1. 这个项目的逻辑流是确定的（拉 diff → 分析 → 生成评审），不需要动态决策和工具选择
2. 不用框架展示你理解底层原理，而不是只会用高层抽象
3. 代码更轻量、更容易 debug、面试官更容易读懂

---

## 四、Agent 核心逻辑（Review Engine）

### 4.1 评审流程

```
接收 PR 事件
    │
    ▼
Step 1: 拉取 PR 信息
    - PR 标题、描述、标签
    - 改动文件列表（路径 + 改动行数）
    - 完整 diff
    │
    ▼
Step 2: 预处理和分流
    - 过滤无需评审的文件（lock 文件、自动生成代码、纯配置变更）
    - 按文件改动大小排序
    - 如果 diff 总量超过 token 上限，分批处理
    │
    ▼
Step 3: 上下文增强
    - 对每个改动文件，拉取完整文件内容（不只是 diff）
    - 拉取相关文件（import 关系、被改动函数的调用方）
    - 如果有 PR 描述中 @mention 的 issue，拉取 issue 内容
    │
    ▼
Step 4: 分层评审
    4a. PR 级别：生成 summary + 整体评估
    4b. 文件级别：对每个文件独立评审
    4c. 行级别：对具体问题生成 inline comment
    │
    ▼
Step 5: 结果聚合 + 去重
    - 合并重复的评审意见
    - 按严重程度排序
    - 控制评论总数（不超过 15 条，避免刷屏）
    │
    ▼
Step 6: 输出到 GitHub
    - 以 Pull Request Review 的形式提交
    - summary 作为 review body
    - inline comments 关联到具体代码行
```

### 4.2 大 PR 处理策略（关键工程挑战）

这是面试必问点。真实世界的 PR 经常有几十个文件、几千行 diff，远超 LLM 上下文窗口。

**分块策略：**
```python
class DiffChunker:
    """
    将大 PR 的 diff 分成可处理的块。
    
    策略：
    1. 按文件分组（天然边界）
    2. 同一目录/模块的文件尽量放在同一块（保持上下文关联）
    3. 每块控制在 token 预算内（默认 20K tokens）
    4. 超大单文件（如 migration 文件）单独处理或跳过
    """
    
    def chunk(self, diff: PRDiff, token_budget: int) -> list[DiffChunk]:
        # 1. 计算每个文件的 diff token 数
        # 2. 按目录做贪心分组
        # 3. 确保不拆分单个文件的 diff
        pass
```

**优先级排序：**
```python
def prioritize_files(files: list[ChangedFile]) -> list[ChangedFile]:
    """
    不是所有文件都值得 review。优先级：
    
    高优先级：
    - 核心业务逻辑文件（src/ 下的 .py/.ts/.go 等）
    - 改动量大的文件
    - 新增文件（可能引入新模块）
    
    低优先级：
    - 测试文件（通常不需要深度 review）
    - 配置文件（JSON/YAML/TOML）
    - 文档文件（.md）
    
    跳过：
    - lock 文件（package-lock.json, poetry.lock）
    - 自动生成代码（*.generated.*, migrations/）
    - 二进制文件
    """
```

### 4.3 上下文增强（另一个关键工程点）

只看 diff 是不够的。一个好的 reviewer 需要理解改动的上下文——这个函数被谁调用？这个类的其他方法是什么？这个改动符合项目的代码风格吗？

```python
class ContextEnricher:
    """
    为每个改动文件补充必要的上下文。
    
    上下文来源：
    1. 完整文件内容（diff 只展示改动行的前后几行）
    2. 相关文件片段（通过 import/调用关系推断）
    3. PR 描述和关联 issue（理解改动意图）
    4. 项目级上下文：
       - README 摘要（理解项目是做什么的）
       - CONTRIBUTING.md（代码规范）
       - 最近的相关 commit 信息
    """
    
    def enrich(
        self, 
        file: ChangedFile, 
        pr: PullRequest,
        token_budget: int  # 每个文件的上下文 token 预算
    ) -> EnrichedContext:
        pass
```

### 4.4 Prompt 设计

**PR Summary Prompt：**
```
你是一位资深代码审查员。请阅读以下 Pull Request 并生成概要。

## PR 信息
标题: {pr_title}
描述: {pr_description}
作者: {pr_author}

## 改动文件
{file_list_with_stats}

## Diff 内容
{diff_content}

请输出：
1. 一句话总结这个 PR 的目的
2. 主要改动点（按模块分组）
3. 改动规模评估（S/M/L/XL）
4. 潜在风险提示（如果有）

以 JSON 格式输出。
```

**File Review Prompt：**
```
你是一位资深代码审查员，正在评审一个文件的改动。

## PR 背景
{pr_summary}

## 文件信息
路径: {file_path}
语言: {language}

## 完整文件内容（改动前）
{original_file_content}

## Diff
{file_diff}

## 相关上下文
{related_context}

请评审这个文件的改动，关注以下方面：
- 逻辑错误或边界条件遗漏
- 错误处理是否充分
- 命名是否清晰准确
- 是否有性能隐患
- 是否符合项目现有代码风格

不要评论代码格式（空格、缩进等），这些交给 linter。
不要对正确的代码说"looks good"，只输出有实质内容的评审意见。

对每条评审意见，输出：
- file: 文件路径
- line: 行号（diff 中的具体行）
- severity: critical / warning / suggestion / nitpick
- comment: 评审意见（简洁，中文）
- suggestion: 修复建议（如果有的话，给出代码片段）

以 JSON 数组格式输出。如果没有值得评论的问题，输出空数组 []。
```

---

## 五、工程能力展示点（面试核心）

以下每个工程点都是面试官会问的，也是这个项目和"demo级项目"拉开差距的地方。

### 5.1 异步任务处理

PR 评审是个耗时操作（30秒-3分钟），不能同步处理。

```python
# Webhook 接收（必须在 10 秒内响应 GitHub）
@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()
    if payload["action"] in ("opened", "synchronize"):
        # 立即返回 202，不阻塞
        background_tasks.add_task(process_review, payload)
        return Response(status_code=202)

# 实际处理在后台
async def process_review(payload: dict):
    pr_info = extract_pr_info(payload)
    
    # 1. 在 PR 上先发一条"正在评审中"的 comment
    await github.post_status(pr_info, "pending", "Review in progress...")
    
    try:
        result = await review_engine.review(pr_info)
        await github.post_review(pr_info, result)
        await github.post_status(pr_info, "success", f"Review complete: {len(result.comments)} comments")
    except Exception as e:
        await github.post_status(pr_info, "error", "Review failed, see dashboard for details")
        logger.error("Review failed", exc_info=e, pr=pr_info.url)
```

**面试话术：** "GitHub Webhook 要求 10 秒内响应，否则会重试。我的设计是 Webhook handler 只做参数校验就立即返回 202，实际评审放到后台异步任务。评审开始时先在 PR 上发一条 pending 状态，完成后更新为 success 或 error。用户能实时知道评审进度。"

### 5.2 流式处理（Streaming）

对于大 PR，不应该等全部评审完才输出，而是分文件逐步输出。

```python
async def review_streaming(pr_info: PRInfo):
    """
    分文件逐步输出评审结果。
    每完成一个文件的评审，立即作为 inline comment 发送到 GitHub。
    用户可以边收到评审意见边修改代码。
    """
    summary = await generate_pr_summary(pr_info)
    # 先发 summary
    await github.post_review_comment(pr_info, summary)
    
    # 然后逐文件评审、逐个发 inline comment
    for chunk in diff_chunker.chunk(pr_info.diff):
        comments = await review_chunk(chunk, summary)
        for comment in comments:
            await github.post_inline_comment(pr_info, comment)
            # 每发一条都记录到 trace
            trace_logger.log_step("inline_comment", comment)
```

**面试话术：** "大 PR 可能有 30 个文件，全部评审完再一次性输出的话用户要等好几分钟。我做了分文件的流式输出，每评完一个文件的改动就把评审意见发到 GitHub，开发者可以边看评审边改代码，不用干等。"

### 5.3 Token 成本控制和缓存

这是生产级系统必须解决的问题。

```python
class CostController:
    """
    三层成本控制：
    
    1. Prompt Cache
       - 同一个 PR 的 summary 在多次文件评审中复用
       - 项目级上下文（README、代码规范）缓存在内存中
       - 利用 Claude/DeepSeek 的 prompt caching 特性减少输入 token 计费
    
    2. 智能跳过
       - 改动量 < 5 行的小文件，合并到一个 batch 中评审
       - 纯删除的改动（删文件、删代码块）简化评审
       - 已有 linter/CI 覆盖的检查项不重复做
    
    3. 预算上限
       - 每个 PR 设置 token 上限（默认 100K input tokens）
       - 超限后只评审优先级最高的文件
       - Dashboard 上展示每次评审的成本明细
    """
    
    def estimate_cost(self, pr_info: PRInfo) -> CostEstimate:
        """评审前预估成本，超预算提前告警"""
        total_tokens = sum(
            self.estimate_file_tokens(f) for f in pr_info.files
        )
        estimated_cost = total_tokens * self.price_per_token
        return CostEstimate(tokens=total_tokens, cost_usd=estimated_cost)
```

**面试话术：** "我做了三层成本控制。第一层是 prompt cache——同一个 PR 评审多个文件时，PR summary 和项目上下文只算一次输入 token。第二层是智能跳过，改动小于 5 行的文件合并处理，纯删除操作简化评审。第三层是硬预算上限，超了就只评审最关键的文件。Dashboard 上能看到每次评审花了多少钱，哪个步骤最贵。"

### 5.4 可观测性（Observability）

```python
@dataclass
class TraceStep:
    step_name: str          # "fetch_diff" / "generate_summary" / "review_file" 等
    input_summary: str      # 输入摘要（不存完整输入，太大）
    output_summary: str     # 输出摘要
    model: str              # 使用的模型
    input_tokens: int       # 输入 token 数
    output_tokens: int      # 输出 token 数
    cost_usd: float         # 成本（美元）
    latency_ms: int         # 耗时（毫秒）
    status: str             # "success" / "error" / "skipped"
    error_message: str      # 如果失败，错误信息
    timestamp: datetime

class TraceLogger:
    """
    记录一次 PR 评审的完整执行轨迹。
    
    一条典型的 trace：
    [0] fetch_pr_info      | 200ms  | $0.00  | success
    [1] generate_summary   | 3200ms | $0.02  | success | gpt-4o | 5.2K in, 0.8K out
    [2] review_file:src/auth.py  | 4100ms | $0.03 | success | 8.1K in, 1.2K out
    [3] review_file:src/api.py   | 3800ms | $0.02 | success | 6.5K in, 0.9K out
    [4] review_file:tests/test_auth.py | skipped (test file, low priority)
    [5] post_review        | 800ms  | $0.00  | success
    
    Total: 12.1s | $0.07 | 5 comments posted
    """
```

**面试话术：** "每次评审都有完整的 trace，记录每一步的输入/输出/token/成本/延迟。所有 trace 存在数据库里，Dashboard 上可以查看。这不是事后才想到做的——我在写第一行代码之前就设计好了 trace schema，所有评审逻辑都通过 trace decorator 包裹。"

### 5.5 容错和降级

```python
class ReviewEngine:
    async def review_with_fallback(self, pr_info: PRInfo) -> ReviewResult:
        """
        三层容错：
        
        1. 单文件评审失败 → 跳过该文件，继续评审其他文件
           不因为一个文件的问题导致整个评审失败
        
        2. LLM 输出格式错误 → 多级 JSON 修复
           Level 1: 正则提取 JSON 块
           Level 2: 修复常见格式错误（末尾多逗号等）
           Level 3: 让 LLM 重新生成（最多重试 2 次）
           Level 4: 放弃该步骤，记录错误
        
        3. 主模型不可用 → 降级到备用模型
           Claude 挂了 → 切 DeepSeek
           DeepSeek 也挂了 → 切 GPT-4o-mini（更便宜但能用）
           全挂了 → 发通知，不提交评审
        """
```

**面试话术：** "我做了三层容错。单文件级别的隔离——一个文件评审失败不影响其他文件。LLM 输出格式的多级修复——这个我在之前 Darwinian 项目里就做过 5 级 JSON 修复，这里复用了同样的思路。模型级别的降级——主模型不可用时自动切换备用模型，保证服务可用性。"

### 5.6 评论质量控制（防止"噪音评论"）

这是产品体验的关键。如果 agent 输出一堆没用的评论，开发者直接就关了。

```python
class CommentFilter:
    """
    评审意见的质量把关：
    
    1. 去重：相同文件中相似的评论只保留一条
    2. 去噪：过滤纯格式/风格建议（交给 linter）
    3. 数量限制：每个 PR 最多 15 条评论（宁可少说，不要刷屏）
    4. 置信度过滤：LLM 给出 confidence 评分 < 0.7 的不发
    5. 严重程度排序：critical 优先，nitpick 排最后且名额有限（最多 3 条）
    """
    
    def filter_and_rank(self, raw_comments: list[ReviewComment]) -> list[ReviewComment]:
        comments = self._deduplicate(raw_comments)
        comments = self._remove_style_noise(comments)
        comments = self._filter_low_confidence(comments)
        comments = self._rank_by_severity(comments)
        comments = self._apply_limits(comments)
        return comments
```

**面试话术：** "代码评审 agent 最大的问题是噪音。如果 agent 输出 50 条废话评论，开发者看两次就再也不用了。我做了一个评论质量过滤层：去重、去噪、数量限制、置信度过滤、严重程度排序。宁可漏掉一些问题，也不刷屏。这个设计决策是从用户体验出发的，不是从技术实现出发的。"

---

## 六、评测方案

### 6.1 自动化 Eval Pipeline

```python
class EvalPipeline:
    """
    自动化评测，跑在 CI 里（GitHub Actions）。
    
    每次改 prompt 或代码逻辑，自动运行 eval 并对比结果。
    
    评测数据集：
    - 收集 20-30 个有高质量人工 review 的开源 PR
    - 来源：Django、Flask、FastAPI 等知名项目的已合并 PR
    - 每个 PR 保存：diff + 人工 review comments
    
    评测指标：
    1. 覆盖率：人类指出的问题，agent 也指出了多少？
    2. 精确率：agent 指出的问题中，有多少是真正的问题？（人工标注）
    3. 噪音率：agent 输出了多少无意义评论？
    4. 成本：每次评审的平均 token 和美元成本
    5. 延迟：每次评审的平均耗时
    """
```

### 6.2 Eval 集构建方法

```
Step 1: 从知名开源项目的 GitHub 上爬取最近 6 个月的已合并 PR
Step 2: 筛选条件：
        - 有至少 2 条 reviewer 的实质性评论（不是"LGTM"）
        - PR 改动在 5-50 个文件之间
        - 评论涉及代码逻辑问题（不是纯格式）
Step 3: 人工审核 30 个 case，确保评测数据质量
Step 4: 保存为标准化 JSON 格式
```

### 6.3 消融实验

| 实验 | 说明 |
|------|------|
| Full System | 完整系统（上下文增强 + 分层评审 + 质量过滤） |
| - Context | 去掉上下文增强，只发 diff 给 LLM |
| - Filter | 去掉评论质量过滤，所有评论都输出 |
| - Layered Review | 去掉分层评审，一次性评审整个 PR |

每组对比覆盖率、精确率、噪音率的变化。

### 6.4 Eval 报告示例

```markdown
## Eval Report - v0.3.1 (2026-05-15)

### Summary
- Eval set: 30 PRs from Django, Flask, FastAPI
- Model: DeepSeek-V3
- Average cost: $0.08 / PR
- Average latency: 45s / PR

### Metrics
| Metric | v0.3.0 | v0.3.1 | Delta |
|--------|--------|--------|-------|
| Coverage | 42% | 48% | +6% |
| Precision | 65% | 71% | +6% |
| Noise Rate | 23% | 15% | -8% |
| Avg Comments/PR | 8.2 | 6.5 | -1.7 |

### Changes in v0.3.1
- Improved file prioritization (skip lock files)
- Added confidence threshold (0.7)
- Better prompt for inline comments
```

---

## 七、项目结构

```
code-reviewer/
├── README.md                    # 项目介绍、安装指南、架构说明
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml           # 本地开发用
├── .github/
│   └── workflows/
│       ├── ci.yml               # 单元测试 + lint
│       └── eval.yml             # 自动 eval pipeline
│
├── server/                      # 后端
│   ├── __init__.py
│   ├── app.py                   # FastAPI 应用入口
│   ├── config.py                # 配置管理（环境变量）
│   │
│   ├── webhook/                 # GitHub Webhook 处理
│   │   ├── handler.py           # Webhook 接收和分发
│   │   ├── signature.py         # Webhook 签名验证
│   │   └── models.py            # GitHub event 数据模型
│   │
│   ├── github/                  # GitHub API 交互
│   │   ├── client.py            # GitHub API 封装
│   │   ├── diff_parser.py       # Diff 解析
│   │   └── comment_poster.py    # 评论发送
│   │
│   ├── review/                  # 评审核心逻辑
│   │   ├── engine.py            # 评审主流程
│   │   ├── chunker.py           # 大 PR 分块
│   │   ├── context.py           # 上下文增强
│   │   ├── reviewer.py          # LLM 评审调用
│   │   └── filter.py            # 评论质量过滤
│   │
│   ├── llm/                     # LLM 调用层
│   │   ├── client.py            # 多模型统一接口
│   │   ├── prompts.py           # Prompt 模板
│   │   ├── parser.py            # 输出解析 + fallback
│   │   └── cache.py             # Prompt cache 管理
│   │
│   ├── trace/                   # 可观测性
│   │   ├── logger.py            # Trace 记录
│   │   ├── models.py            # Trace 数据模型
│   │   └── cost.py              # 成本计算
│   │
│   ├── db/                      # 数据库
│   │   ├── models.py            # ORM 模型
│   │   ├── migrations/          # 数据库迁移
│   │   └── repository.py        # 数据访问层
│   │
│   └── api/                     # Dashboard API
│       ├── reviews.py           # 评审记录查询
│       ├── traces.py            # Trace 查询
│       └── stats.py             # 统计数据
│
├── dashboard/                   # 前端
│   ├── package.json
│   ├── src/
│   │   ├── App.vue
│   │   ├── views/
│   │   │   ├── ReviewList.vue   # 评审历史
│   │   │   ├── TraceView.vue    # Trace 详情
│   │   │   └── StatsView.vue    # 统计面板
│   │   └── components/
│   │       ├── TraceTimeline.vue # Trace 时间线组件
│   │       └── CostBadge.vue    # 成本展示组件
│   └── ...
│
├── eval/                        # 评测
│   ├── dataset/                 # 评测数据集
│   │   └── cases.json
│   ├── run_eval.py              # 运行评测
│   ├── analyze.py               # 分析结果
│   └── reports/                 # 历史 eval 报告
│
├── prompts/                     # Prompt 模板（Jinja2）
│   ├── summary.j2
│   ├── file_review.j2
│   └── inline_comment.j2
│
└── tests/                       # 测试
    ├── test_diff_parser.py
    ├── test_chunker.py
    ├── test_filter.py
    ├── test_cost.py
    └── fixtures/                # 测试用 PR diff 数据
```

---

## 八、实现路线图（8 周）

### 第 1-2 周：基础设施 + GitHub 集成

**Week 1：项目骨架 + GitHub App**
- [ ] 创建 GitHub App，获取 App ID 和 Private Key
- [ ] 搭建 FastAPI 项目骨架
- [ ] 实现 Webhook 接收和签名验证
- [ ] 实现 GitHub API 封装（获取 PR 信息、diff、发评论）
- [ ] 本地用 ngrok 测试 Webhook 链路

**Week 2：Diff 解析 + 基本评审**
- [ ] 实现 diff 解析器（支持 unified diff 格式）
- [ ] 实现基本的 LLM 调用封装（先接一个模型）
- [ ] 实现最简版评审逻辑：拿到 diff → 发给 LLM → 把结果发到 PR
- [ ] 端到端跑通：一个真实 PR 能收到 agent 评论

**Week 2 检查点：** 在真实 GitHub PR 上看到 agent 发出的评审评论

### 第 3-4 周：评审质量提升

**Week 3：分层评审 + 上下文增强**
- [ ] 实现分层评审逻辑（summary → file review → inline comments）
- [ ] 实现上下文增强（拉取完整文件、相关文件、PR 描述）
- [ ] 实现大 PR 分块策略
- [ ] 设计和迭代 prompt 模板

**Week 4：质量控制 + 容错**
- [ ] 实现评论质量过滤（去重、去噪、数量限制、置信度）
- [ ] 实现 LLM 输出的多级 JSON 解析
- [ ] 实现模型降级策略
- [ ] 实现单文件级别的错误隔离
- [ ] 在 5-10 个真实 PR 上测试，手动评估质量

**Week 4 检查点：** 在 10 个真实 PR 上，评审质量达到"大部分评论有价值"

### 第 5-6 周：工程化 + Dashboard

**Week 5：可观测性 + 成本控制**
- [ ] 实现 Trace 日志系统
- [ ] 实现成本计算和预算控制
- [ ] 实现 prompt cache
- [ ] 接入第二个 LLM（支持模型切换）
- [ ] 数据库设计和 ORM 实现

**Week 6：Dashboard 开发**
- [ ] Dashboard 前端开发（Vue.js）
  - 评审历史列表
  - Trace 时间线详情
  - 成本和延迟统计
- [ ] Dashboard API 开发
- [ ] 前后端联调

**Week 6 检查点：** Dashboard 可用，能查看评审历史和 trace 详情

### 第 7-8 周：评测 + 部署 + 打磨

**Week 7：Eval Pipeline + 部署**
- [ ] 构建评测数据集（30 个高质量 PR case）
- [ ] 实现自动化 eval 脚本
- [ ] 跑第一轮完整 eval，记录基线
- [ ] Dockerfile + 部署到云平台
- [ ] 配置域名和 HTTPS

**Week 8：打磨 + 文档**
- [ ] 基于 eval 结果优化 prompt 和逻辑
- [ ] 跑消融实验
- [ ] 跑跨模型对比
- [ ] 写 README（安装指南 + 架构说明 + 评测结果）
- [ ] 写一篇技术博客（讲清架构决策）
- [ ] 准备面试叙事

**Week 8 检查点：** 
- 部署地址可用，面试官能直接安装
- Eval 报告有数据
- README 和博客完成

---

## 九、面试叙事

### 30 秒版本
"我做了一个 GitHub 代码评审 Agent，部署在线上，安装到仓库后每次提交 PR 自动触发评审，在 PR 页面直接给出 inline comment。工程上我重点解决了几个问题：大 PR 的分块处理、评论质量控制防止刷屏、三层容错保证服务可用性、完整的可观测性系统追踪每一步的 token 和成本。目前在 30 个开源 PR 的评测集上，评审覆盖率 X%，精确率 Y%。您可以直接安装试用。"

### 面试官高频问题

**Q: 为什么做代码评审 agent？市面上不是有 CodeRabbit、Cursor 这些了吗？**
A: "两个原因。一是这个场景天然适合展示全栈工程能力——Webhook 集成、异步处理、流式输出、可观测性、评测体系，每一个都是生产级系统需要的。二是我想证明自己能做到的工程质量标准：面试官打开链接就能用，不是一个只能本地跑的 demo。和 CodeRabbit 的区别是，我这个是完全开源的、架构透明的，我能讲清楚每一个设计决策。"

**Q: 你的 agent 和直接把 diff 发给 ChatGPT 有什么区别？**
A: "区别在工程层面。直接发给 ChatGPT 面临三个问题：大 PR 超过上下文窗口，只看 diff 不理解上下文，输出质量不可控。我的系统做了分块处理（大 PR 按文件切分、按优先级排序）、上下文增强（自动拉取完整文件和相关代码）、评论质量过滤（去重去噪、数量限制、置信度阈值）。这些就是'能用'和'好用'的区别。"

**Q: 评审质量怎么样？有没有量化数据？**
A: "我构建了一个 30 个 PR 的评测集，来自 Django、Flask、FastAPI 等项目的真实已合并 PR，每个都有人工 review 评论。在这个评测集上，我的系统评审覆盖率 X%（人类指出的问题中 agent 也指出了 X%），精确率 Y%（agent 指出的问题中 Y% 是真正的问题）。每次改 prompt 或逻辑都会自动跑一遍 eval，确保不退化。"

**Q: 成本控制怎么做的？**
A: "三层。第一层 prompt cache，同一个 PR 的项目上下文和 summary 只生成一次，评审多个文件时复用。第二层智能跳过，lock 文件、自动生成代码、改动小于 5 行的文件不浪费 token。第三层硬预算上限，超了只评审最关键的文件。Dashboard 上能看到每次评审的成本明细——哪个文件花了多少钱、每一步的 token 消耗。平均每个 PR 评审成本 $0.05-0.10。"

**Q: 如果 LLM 返回的格式不对怎么办？**
A: "四级 fallback。第一级，用正则从 LLM 输出中提取 JSON 块（LLM 经常在 JSON 前后加文字说明）。第二级，修复常见格式错误（末尾多逗号、单引号替换双引号）。第三级，重新调一次 LLM，prompt 里加上'请确保输出纯 JSON'的强约束。第四级，放弃该步骤，记录错误到 trace，继续处理下一个文件。这个经验来自我之前 Darwinian 项目的五级 JSON 修复。"

**Q: 为什么不用 LangChain / LangGraph？**
A: "两个原因。第一，这个评审流程是确定性的管道（拉 diff → 分块 → 评审 → 过滤 → 发评论），不需要动态决策和工具选择，用框架反而增加复杂度。第二，我之前三个项目都用了 LangGraph，这次特意不用，就是为了证明我理解底层实现，不依赖框架也能写出结构清晰的 agent 系统。面试官可以直接看代码，没有框架的间接层挡着。"

---

## 十、产出清单（面试前确保完成）

| 产出 | 说明 | 重要程度 |
|------|------|----------|
| GitHub 仓库 | 代码质量 > star 数。Clean commit history，有 CI | ⭐⭐⭐⭐⭐ |
| 部署地址 | 面试官能直接安装到自己的 repo 试用 | ⭐⭐⭐⭐⭐ |
| Dashboard | 能看到评审历史、trace 详情、成本统计 | ⭐⭐⭐⭐ |
| Eval 报告 | 有量化指标（覆盖率、精确率、成本、延迟） | ⭐⭐⭐⭐ |
| README | 架构图 + 安装指南 + 设计决策说明 | ⭐⭐⭐⭐ |
| 技术博客 | 一篇，讲清楚核心架构决策和 trade-off | ⭐⭐⭐ |
| 消融实验数据 | 证明每个工程模块的贡献 | ⭐⭐⭐ |

---

## 十一、成本估算

### API 成本
- 开发阶段：~$20（调试 + prompt 迭代）
- Eval 运行：~$10（30 case × 多轮）
- 上线后日常：$0.05-0.10 / PR
- 总预算：$50-80

### 部署成本
- Railway / Fly.io 免费额度通常够用
- 域名：~$10/年
- 数据库：SQLite 开发阶段免费，PostgreSQL 用 Supabase 免费额度

### 时间投入
- 8 周，每周投入 20-30 小时
- 前 4 周最密集（基础设施 + 核心逻辑）
- 后 4 周相对轻松（打磨 + 评测 + 部署）

---

## 十二、风险和应对

| 风险 | 应对 |
|------|------|
| GitHub App 审批慢 | 开发阶段用个人安装模式，不需要上架 Marketplace |
| 评审质量不够好（噪音多） | 重点投入质量过滤层，宁可少输出不刷屏 |
| 大 PR 评审太慢（>5分钟） | 设置超时，超时后只输出已完成部分 |
| Eval 数据集构建耗时 | 先用 10 个 case 跑通流程，后期再扩充到 30 个 |
| 前端开发占用太多时间 | Dashboard 从简，先做核心功能（评审列表 + trace），统计面板放最后 |
| 面试官不愿意安装到自己 repo | 准备几个演示 PR 的录屏，以及一个公开的演示仓库 |
