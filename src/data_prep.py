"""
data_prep.py — 准备 MATH SFT 训练数据

干啥的:
    从 Hugging Face 上的 MATH 数据集 (Hendrycks et al. 2021) 加载训练集,
    把每道题的 (problem, solution) 转成 ChatML 格式, 写入 jsonl, 用于 SFT.

输入:  hendrycks/competition_math (从 HuggingFace 自动下载, ~10MB)
输出:  data/sft_train.jsonl     每行: {"messages": [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}

什么时候跑:
    Week 1 Day 3-4, 在 L20 服务器上跑 (Mac 也能跑, 因为只是文件处理 + HF 下载)

依赖:
    pip install datasets

跑法:
    python -m src.data_prep --split train --out data/sft_train.jsonl
    python -m src.data_prep --split test  --out data/sft_test.jsonl    # 评测时用 train 还是 test 取决于 eval 实现

为什么这么简单:
    MATH 数据集本身就有标准答案 + 完整解答过程 (作者写的),
    所以不像 τ-bench 那样需要 GPT-4o 帮你生成训练轨迹.
    直接拿现成的就能用. 这就是 RLVR 类任务比对话类任务好搞的原因之一.
"""

import argparse
import json
from pathlib import Path


SYSTEM_PROMPT = (
    "You are a math problem solver. Solve the problem step by step, "
    "showing your reasoning. Put your final answer inside \\boxed{}."
)


def format_as_chatml(problem: str, solution: str) -> dict:
    """把一道 MATH 题转成 ChatML 格式. 训练时 user 部分不算 loss, assistant 算."""
    return {
        "messages": [
            {"role": "system",    "content": SYSTEM_PROMPT},
            {"role": "user",      "content": problem.strip()},
            {"role": "assistant", "content": solution.strip()},
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="train", choices=["train", "test"],
                        help="MATH 数据集的 split, train ~7500 题, test ~5000 题")
    parser.add_argument("--out", type=Path, default=Path("data/sft_train.jsonl"),
                        help="输出 jsonl 文件路径")
    parser.add_argument("--max_samples", type=int, default=None,
                        help="只取前 N 条 (调试用), 默认全量")
    parser.add_argument("--dataset", default="hendrycks/competition_math",
                        help="HuggingFace 数据集名")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    # TODO Day 3-4 实现:
    #   from datasets import load_dataset
    #   ds = load_dataset(args.dataset, split=args.split)
    #   if args.max_samples: ds = ds.select(range(args.max_samples))
    #   with open(args.out, "w") as f:
    #       for ex in ds:
    #           # MATH 数据集字段名: "problem" 和 "solution"
    #           # solution 里通常已经包含 \boxed{...} 最终答案
    #           f.write(json.dumps(format_as_chatml(ex["problem"], ex["solution"])) + "\n")
    #   print(f"✅ wrote {len(ds)} examples to {args.out}")

    print(f"[骨架] 准备从 {args.dataset} ({args.split}) 加载数据 → {args.out}")
    print("[骨架] Day 3-4 实现具体逻辑")


if __name__ == "__main__":
    main()
