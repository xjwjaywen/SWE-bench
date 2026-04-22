# Generative Agents — 复现 Stanford 2023

参考论文: [Generative Agents: Interactive Simulacra of Human Behavior (Park et al., 2023)](https://arxiv.org/abs/2304.03442)

## 进度

- [x] Day 1 — 两个 agent 对话 + 极简 memory stream
- [ ] Day 2 — 三因子检索 (recency × relevance × importance)
- [ ] Day 3 — reflection 触发与生成
- [ ] Day 4+ — 多 agent + 世界模型 + 事件注入

## 运行 Day 1

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export MINIMAX_API_KEY="你的 key"
python day1.py
```

预期输出: Isabella 和 Maria 在 Hobbs Cafe 进行 8 轮自然对话,结尾打印双方的 memory stream。
