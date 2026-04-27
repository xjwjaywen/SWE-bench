# Multi-Agent RL System on τ-bench

> 用 RL 联合训练 3 个专精 agent (Planner / Tool-caller / Responder),在 τ-bench 客服任务上超过 GPT-4o 基线。

## 目标 (resume bullet)

- 3 specialist LoRA adapters on Qwen2.5-7B
- Joint reinforcement learning with credit assignment
- τ-airline benchmark: base **12%** → SFT **~25%** → multi-agent + RL **~42%** (target)
- **超过 GPT-4o 基线 36%**,用 7B 模型

## 路线图

| 版本 | 内容 | 简历价值 | 预计周数 |
|---|---|---|---|
| **v0.1** | 单 agent + SFT (LoRA) | 学会训练流程 | Week 1-3 |
| v0.2 | 单 agent + DPO 偏好优化 | 学会用偏好数据 | Week 4-6 |
| v0.3 | 单 agent + GRPO 真 RL | 真正的 agent 项目 | Week 7-12 |
| v0.4 | 多 agent + 联合 GRPO | multi-agent RL 旗舰 | Week 13-16 |

## 当前状态:Phase 2 — 环境搭建中

- [x] 项目骨架建立
- [ ] L20 服务器登入 (本周)
- [ ] Mac 本地 env (transformers + datasets + openai)
- [ ] 跑通 Unsloth 官方 demo
- [ ] τ-bench baseline 评测 (拿到 12% 数字)

详见 [`notes/week1_checklist.md`](notes/week1_checklist.md)

## 项目结构

```
src/
  data_prep.py    # 用 GPT-4o 在 τ-bench 训练集上生成成功轨迹 → SFT 数据
  train.py        # SFT 训练 Qwen2.5-7B + LoRA
  eval.py         # 在 τ-bench 测试集上评测
data/             # SFT 数据 (gitignored)
outputs/          # 训练产出 (gitignored)
notes/            # 学习笔记 / 检查清单
```

## 快速开始 (Phase 2 完成后启用)

```bash
# 1. 装环境
pip install -r requirements.txt

# 2. 配置 API key
cp .env.example .env  # 编辑填入真实 key

# 3. 准备 SFT 数据 (Week 2 Day 1-3, 用 GPU 不需要)
python -m src.data_prep --num_tasks 100 --out data/sft_train.jsonl

# 4. 跑 baseline 评测 (Week 1 Day 5-7, 需要 GPU)
python -m src.eval --bench airline --num_tasks 50

# 5. SFT 训练 (Week 2 Day 4-5, 需要 GPU, ~4-8 小时)
python -m src.train --data data/sft_train.jsonl --out outputs/v01_sft

# 6. 训练后再评测 (Week 2 Day 6-7)
python -m src.eval --bench airline --num_tasks 50 --lora outputs/v01_sft
```

## 参考

- τ-bench: https://github.com/sierra-research/tau-bench
- Unsloth (LoRA 训练加速): https://github.com/unslothai/unsloth
- TRL (Hugging Face 训练库): https://github.com/huggingface/trl
- Qwen2.5-7B-Instruct: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
