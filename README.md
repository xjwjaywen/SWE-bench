# Multi-Agent RL System on MATH (RLVR)

> 用 RL 联合训练 3 个专精 agent (Proposer / Verifier / Corrector),在 MATH 高中竞赛数学 benchmark 上验证 DeepSeek-R1 RLVR 方法在 consumer-scale 硬件上的可迁移性。

## 目标 (resume bullet)

> Replicated DeepSeek-R1 RLVR methodology on a 4× L20 GPU node:
> - 3 specialist LoRA adapters on Qwen2.5-7B (Proposer / Verifier / Corrector)
> - Joint GRPO training with custom credit assignment
> - **MATH benchmark: base 50% → SFT 55% → single-agent GRPO 62% → multi-agent GRPO ~65%** (target)
> - Distributed training with DeepSpeed ZeRO-2 across 4 L20 GPUs

## 项目实质

```
INPUT: "If x² - 5x + 6 = 0, find x."

[Proposer]:    x² - 5x + 6 = (x-2)(x-3) = 0,  so x = 2 or x = 3
[Verifier]:    Step 1 ✅ factoring correct
                Step 2 ✅ roots correct
[Final]:       \boxed{x \in \{2, 3\}}

EVALUATOR (程序判, 0 API 费用):
  从 \boxed{} 提取答案 → 和 ground truth 比对 → ✅ / ❌
```

不是 chatbot — 是**多步推理 + 自我验证 + 自我修正**的 agent 系统。

## 路线图

| 版本 | 内容 | 算力需求 | 预计周数 |
|---|---|---|---|
| **v0.1** | 单 agent + SFT (LoRA) on MATH train set | 1 卡, 4-8h | Week 1-3 |
| v0.2 | + DPO 偏好优化 | 1 卡, 8-12h | Week 4-6 |
| v0.3 | + GRPO 单 agent 真 RL | 2 卡, 1-2d | Week 7-12 |
| v0.4 | 3 agents 联合 GRPO + credit assignment | 4 卡, 3-7d | Week 13-16 |

## 当前状态:Phase 2 — 环境搭建中

- [x] 项目骨架建立
- [x] L20 服务器登入 (4× L20 48GB 节点)
- [ ] Mac 本地 env (transformers + datasets)
- [ ] 服务器 conda env + GPU PyTorch
- [ ] 跑通 Unsloth Qwen2.5-7B 加载
- [ ] MATH baseline 评测 (拿到 ~50% 数字)

详见 [`notes/week1_checklist.md`](notes/week1_checklist.md)

## Benchmark: MATH

- **Hendrycks et al., 2021**: 12,500 道高中数学竞赛题(代数 / 几何 / 数论 / 概率 / 微积分预备)
- **完全开源**: https://huggingface.co/datasets/hendrycks/competition_math
- **0 API 费**: 答案在 `\boxed{X}` 里,程序提取直接和 ground truth 比对
- **Leaderboard 完整**: GPT-4o / Claude / DeepSeek-R1 都报这个数,可以横向比

```
公开数字 (作为参照):
  Qwen2.5-7B-Instruct:    ~50%
  Qwen2.5-Math-7B:        ~83%   (数学专门预训练)
  GPT-3.5:                ~35%
  Claude 3 Sonnet:        ~73%
  GPT-4o:                 ~76%
  DeepSeek-R1-Distill-7B: ~92%   (从 671B 蒸馏, 不可比)
```

我们的目标:**Qwen2.5-7B 50% → 65±5%**,在 single-node 4× L20 上,展示 R1 方法可缩放到 consumer 级硬件。

## 项目结构

```
src/
  data_prep.py    # 从 MATH 数据集准备 SFT/RL 训练数据
  train.py        # SFT 训练 Qwen2.5-7B + LoRA
  eval.py         # MATH 评测 (程序判答案, 无 API)
data/             # 训练数据 (gitignored)
outputs/          # 训练产出 (gitignored)
notes/            # 学习笔记 / 检查清单
```

## 快速开始 (Phase 2 完成后启用)

```bash
# 1. 装环境 (服务器上)
conda create -n agentrl python=3.10 -y
conda activate agentrl
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
pip install unsloth trl bitsandbytes peft accelerate

# 2. 准备 SFT 数据 (从 MATH train set 直接构造, 不需要外部 API)
python -m src.data_prep --split train --out data/sft_train.jsonl

# 3. 跑 baseline 评测 (Qwen2.5-7B 在 MATH 上的原始能力)
CUDA_VISIBLE_DEVICES=2 python -m src.eval --num_problems 100

# 4. SFT 训练 (1 卡, 4-8 小时)
CUDA_VISIBLE_DEVICES=2 python -m src.train --data data/sft_train.jsonl --out outputs/v01_sft

# 5. 训练后再评测
CUDA_VISIBLE_DEVICES=2 python -m src.eval --num_problems 100 --lora outputs/v01_sft
```

## 参考

- DeepSeek-R1 论文: https://arxiv.org/abs/2501.12948 (方法论源头)
- MATH dataset: Hendrycks et al. 2021, https://arxiv.org/abs/2103.03874
- Unsloth (LoRA 训练加速): https://github.com/unslothai/unsloth
- TRL (Hugging Face 训练库): https://github.com/huggingface/trl
- Qwen2.5-7B-Instruct: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
