"""
data_prep.py — 准备 SFT 训练数据

干啥的:
    从 τ-bench 的训练任务里, 用 GPT-4o 跑一遍, 把成功的对话轨迹
    抠出来, 按 ChatML 格式存成 jsonl, 用于 train.py 微调.

输入:  τ-bench 任务 (从 tau_bench 库读, 不需要本地数据文件)
输出:  data/sft_train.jsonl  (每行一个 {"messages": [...]})

什么时候跑:
    Week 2 Day 1-3, 在 Mac 上跑就行 (纯 API 调用, 不需要 GPU)

依赖 (Week 2 装):
    pip install openai
    pip install git+https://github.com/sierra-research/tau-bench.git

跑法:
    export OPENAI_API_KEY=sk-...
    python -m src.data_prep --num_tasks 100 --out data/sft_train.jsonl
"""

import argparse
import json
from pathlib import Path


def collect_successful_trajectory(task) -> list[dict] | None:
    """
    用 GPT-4o 跑一次 τ-bench 任务, 如果任务成功就返回这次对话的 messages.
    任务失败返回 None (我们只要成功的轨迹做 SFT 数据).

    返回格式: [{"role": "system"/"user"/"assistant", "content": "..."}]

    TODO Week 2 实现:
        1. 用 tau_bench 的 env 加载这个 task
        2. 跑 GPT-4o 当 agent, env 自带的 user_simulator 当用户
        3. 多轮对话直到任务结束
        4. 用 task.evaluate() 判断是否成功
        5. 成功就返回对话历史, 失败返回 None
    """
    raise NotImplementedError("Week 2 实现")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_tasks", type=int, default=100,
                        help="跑多少个训练任务尝试生成轨迹")
    parser.add_argument("--out", type=Path, default=Path("data/sft_train.jsonl"),
                        help="输出 jsonl 文件路径")
    parser.add_argument("--bench", default="airline", choices=["airline", "retail"],
                        help="τ-bench 子集")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    # TODO Week 2:
    #   1. 从 tau_bench 加载 args.bench 的训练任务列表
    #   2. for task in tasks[:args.num_tasks]:
    #          messages = collect_successful_trajectory(task)
    #          if messages: 写入 args.out 一行 json.dumps({"messages": messages})
    #   3. 打印统计: 跑了 N 个, 成功 M 个, 成功率 M/N

    print(f"[骨架] 准备从 τ-{args.bench} 生成 {args.num_tasks} 条数据 → {args.out}")
    print("[骨架] Week 2 实现具体逻辑")


if __name__ == "__main__":
    main()
