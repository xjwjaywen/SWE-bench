# Week 1 检查清单

> 目标: 在 4× L20 节点上验证训练能跑通 + 拿到 Qwen2.5-7B 在 MATH 上的 baseline 数字

## 硬件 (你已经确认 ✅)

```
节点: 4× NVIDIA L20 (各 48GB)
驱动: 570.133.20 / CUDA 12.8
你的工作目录: /data/xjw/

GPU 0, 1: 别人在用小进程, 别动
GPU 2, 3: 空闲, 你用这两张
始终用: export CUDA_VISIBLE_DEVICES=2,3
```

## Mac 本地 (准备工作)

- [ ] `python --version` ≥ 3.10
- [ ] `pip install -r requirements.txt` (Mac 那部分包)
- [ ] `cp .env.example .env` (v0.1 不需要任何 key, 留空就行)

## L20 服务器 — Day 1: 环境搭建

```bash
# SSH 上去之后
cd /data/xjw

# 1. 创建项目专用 conda env
conda create -n agentrl python=3.10 -y
conda activate agentrl

# 2. 装 GPU PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 3. 验证 4 张 GPU 都能看到
python -c "
import torch
print('CUDA:', torch.cuda.is_available())
print('GPU count:', torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    p = torch.cuda.get_device_properties(i)
    print(f'  GPU {i}: {p.name} ({p.total_memory/1e9:.1f}GB)')
"

# 4. clone 项目 (服务器要能访问 github, 可能需要配代理或用 SSH key)
git clone https://github.com/xjwjaywen/SWE-bench.git agentrl-project
cd agentrl-project

# 5. 装项目依赖 + 训练栈
pip install -r requirements.txt
pip install unsloth trl bitsandbytes peft accelerate
```

## L20 服务器 — Day 2: 验证训练库

```bash
# 始终用空闲卡 2,3
export CUDA_VISIBLE_DEVICES=2

# 验证 Unsloth 能加载 Qwen2.5-7B (会下载 ~5GB 模型, 10-30 分钟)
python -c "
from unsloth import FastLanguageModel
model, tok = FastLanguageModel.from_pretrained(
    'unsloth/Qwen2.5-7B-Instruct',
    max_seq_length=2048,
    load_in_4bit=True,
)
print('✅ Qwen2.5-7B 加载成功')
import torch
print(f'显存占用: {torch.cuda.memory_allocated()/1e9:.2f} GB')
"
```

## L20 服务器 — Day 3-4: 准备 MATH 数据 + baseline

```bash
# 准备 SFT 训练数据 (从 MATH train set 直接构造, 不要 API)
python -m src.data_prep --split train --out data/sft_train.jsonl

# 看一下生成了多少条
wc -l data/sft_train.jsonl   # 期望 ~7500 条

# 跑 baseline 评测 (Qwen2.5-7B-Instruct 在 MATH test 上的原始能力)
# 100 题大约 30-60 分钟
CUDA_VISIBLE_DEVICES=2 python -m src.eval --num_problems 100

# 期望输出: accuracy ≈ 50% (公开数字 ~50-55%, 你跑出来在这个范围就对)
```

## Week 1 完成标志

```
GitHub README 状态部分应该都打勾:
- [x] L20 服务器登入
- [x] Mac 本地 env
- [x] 服务器 conda env + GPU PyTorch
- [x] Unsloth Qwen2.5-7B 加载成功
- [x] MATH baseline 拿到 ~50% 数字
```

完成 = 你已经超过 80% 「想学训练但卡在装环境」的人。

## 警告:别做的事

```
❌ 看 YouTube LoRA 教程 (动手做更快)
❌ 重读书的 Ch 1-9 (跟你目标无关)
❌ 写「v0.1 详细技术规划」文档 (代码就是文档)
❌ 想「我是不是该先精通 PyTorch」(不需要,卡住了再问)
```

每天醒来问自己: **「今天有跑过任何 GPU 命令吗?有数字产生吗?」** 没有 = 在伪装进度。
