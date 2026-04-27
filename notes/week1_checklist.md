# Week 1 检查清单

> 目标: 验证你能在 L20 上把训练跑起来 + 拿到 baseline 数字

## 不需要 GPU (Mac 本地能做)

- [ ] **去问实验室 L20 哪天能登上** ← 今天必做
- [ ] Mac 装 Python 3.10+ (推荐 `pyenv` 或 `conda`)
- [ ] `pip install -r requirements.txt` (Week 1 那块,不装 GPU 包)
- [ ] `cp .env.example .env`,填入真实 OPENAI_API_KEY
- [ ] 浏览 https://github.com/sierra-research/tau-bench 的 README
  - 看「Tasks」一节,理解一个 task 是什么样
  - 看「Evaluation」一节,知道怎么判分
  - **15 分钟扫读**,不要精读

## 需要 L20 (服务器登上后)

### Day 1-2: 硬件 / 环境验证
- [ ] ssh 登入 L20 服务器
- [ ] `nvidia-smi` 看到 L20 + 48GB 显存
- [ ] 装 conda 环境 `python=3.10`
- [ ] 装 GPU PyTorch: `pip install torch --index-url https://download.pytorch.org/whl/cu121`
- [ ] 验证:
  ```bash
  python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name())"
  ```
  应该输出 `True NVIDIA L20`

### Day 3-4: 训练库验证
- [ ] `pip install unsloth trl bitsandbytes peft accelerate datasets`
- [ ] 跑 unsloth 官方 demo (任意数据,验证训练能跑通):
  https://github.com/unslothai/unsloth#-finetune-for-free
- [ ] 看到 loss 数字下降,训完保存了一个 LoRA 文件 → ✅

### Day 5-7: τ-bench baseline
- [ ] `pip install git+https://github.com/sierra-research/tau-bench.git`
- [ ] `python -m src.eval --num_tasks 50` (用 base Qwen2.5-7B 跑,无 LoRA)
- [ ] 记录数字 → 大约 **10-15%**,这是你的 baseline

## Week 1 完成标志

```
你的 GitHub README 状态部分:
- [x] L20 服务器登入
- [x] Mac 本地 env (transformers + datasets + openai)
- [x] 跑通 Unsloth 官方 demo
- [x] τ-bench baseline 评测 (拿到 12% 数字)
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
