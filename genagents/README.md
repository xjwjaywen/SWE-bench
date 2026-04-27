# Generative Agents 多日社会模拟平台

> 独立复现 Stanford *Generative Agents: Interactive Simulacra of Human Behavior* (Park et al., 2023) 核心架构,在 paper §5 评估方法之上扩展四字段 L0-L3 分级 + 关注度数值化矩阵,捕捉 paper 二元 density 指标无法表达的关系演化。

## 核心数字

- **3 天 3-agent 模拟,paper-faithful 信息扩散覆盖率 100%, L3 完整覆盖率 100%** (seed event = 2026-02-14 Hobbs Cafe 情人节 party)
- **关系矩阵捕捉 asymmetric 演化**:Klaus → Isabella attention = 152 vs Maria → Klaus = 32,paper density 指标无法表达
- **1 天 9-18 时段实测成本 ¥0.31**,3 天完整 run 估算 ≈ ¥1-2,SEED 控制可复现
- **Streamlit dashboard** 可视化所有核心指标

## Demo 截图

![Dashboard](docs/dashboard.png)

(若无截图请运行 `streamlit run dashboard.py` 查看)

## 架构

完整复现 Park 2023 §4:

- **Memory Stream** — 每 agent 一个 append-only timeline
- **Importance** — 每条 memory 由 LLM 评 1-10 分
- **Three-factor retrieval** — `score = recency + relevance + importance`
- **Reflection** — importance buffer ≥ 30 自动触发,生成 3 条抽象判断,存入同一 memory stream
- **Daily plan** — 三因子检索 top-10 + pin 最近 3 条 reflection,生成 24 小时时间表
- **Hourly time-step + co-location conversation** — 同地点 80% 概率随机配对触发对话
- **Multi-day memory continuity** — 跨天 reflection 影响今日 plan

## 技术栈

- Python 3.11+ / asyncio
- MiniMax M2-Stable(OpenAI 兼容 API)
- sentence-transformers + BGE-small-zh(本地 embedding,~100MB)
- Altair + Streamlit + Pandas(可视化)

## 评估方法

| 指标 | 来源 | 作用 |
|---|---|---|
| Paper-faithful yes/no 覆盖率 | paper §5.2.2 | 二元主指标 |
| **L0-L3 四字段分级** | **本项目扩展** | 小规模实验下 yes/no 粒度不够时提供细化 |
| **Known fields 追踪** | **本项目扩展** | 字段级诊断:哪个字段最先丢 |
| **关注度 attention** | **本项目扩展** | `count × Σ importance`,补充 paper density |
| **Top-3 reflection 原文** | **本项目扩展** | 替代 sentiment 数值化,直接展示关系质感 |

## Key Findings(3 天模拟)

1. **信息完整度随时间演化**:L3 覆盖率 67% (Day 1 末) → 100% (Day 3 末)
2. **关系 asymmetry 可双向修复**:Maria → Isabella 反思 0 → 11 条
3. **关系 asymmetry 可单向停滞**:Klaus → Maria 反思 4 → 16 条,但 Maria → Klaus 保持 4 条 — paper density 指标无法捕捉这种"主动 vs 保留"的关系动态

## 快速开始

```bash
pip install -r requirements.txt
export MINIMAX_API_KEY="..."
export MINIMAX_MODEL="MiniMax-M2-Stable"

# 完整 3 天模拟(30 分钟,¥1-2)
python day6.py

# 快速 1 天验证(10 分钟,¥0.3)
NUM_DAYS=1 HOURS_START=9 HOURS_END=18 python day6.py

# 可视化
streamlit run dashboard.py
```

## 演化路径

| Day | 实现 |
|---|---|
| Day 1 | 2 agent 对话 + 极简 memory stream |
| Day 2 | 三因子检索 + LLM importance 评分 |
| Day 3 | Reflection 自动触发 + 高层抽象 |
| Day 4 | 日计划生成 + 小时粒度 + 多 agent 调度 |
| Day 5 | 第 3 个 agent + 信息传播实验 |
| Day 6 | 多天模拟 + paper-faithful 评估 + markdown 报告 |
| Day 7 | Streamlit dashboard + SEED 控制 + cost 追踪 |

## 参考

- Park et al., *Generative Agents: Interactive Simulacra of Human Behavior*, 2023, [arXiv:2304.03442](https://arxiv.org/abs/2304.03442)
- Park et al., *Generative Agent Simulations of 1,000 People*, 2024, [arXiv:2411.10109](https://arxiv.org/abs/2411.10109)
