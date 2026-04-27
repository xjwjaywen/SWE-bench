"""
eval.py — 在 τ-bench 上评测模型

干啥的:
    加载模型 (base 或 base + LoRA), 在 τ-bench 测试集上跑评测,
    报告任务成功率 (你简历上要的那个数字).

输入:  --lora 路径 (可选, 不给就跑 baseline 不带 LoRA)
输出:  控制台打印准确率 + outputs/eval_results.json

什么时候跑:
    Week 1 Day 5-7: python -m src.eval
        → 拿到 baseline 数字 (大约 12% on τ-airline)
    Week 2 Day 6-7: python -m src.eval --lora outputs/v01_sft
        → 拿到 SFT 后的数字, 应该 > baseline 才算训练成功

依赖 (Week 2 在 L20 装):
    pip install torch unsloth peft
    pip install git+https://github.com/sierra-research/tau-bench.git

跑法:
    python -m src.eval                              # baseline (无 LoRA)
    python -m src.eval --lora outputs/v01_sft       # SFT 后
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lora", type=Path, default=None,
                        help="LoRA 文件夹路径, 不给就跑 base 模型 baseline")
    parser.add_argument("--bench", default="airline", choices=["airline", "retail"],
                        help="τ-bench 子集")
    parser.add_argument("--num_tasks", type=int, default=50,
                        help="评测多少个任务, 越多越准但越慢")
    parser.add_argument("--model", default="unsloth/Qwen2.5-7B-Instruct",
                        help="base 模型")
    parser.add_argument("--out", type=Path, default=Path("outputs/eval_results.json"),
                        help="评测结果保存路径")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    # TODO Week 1-2:
    #   1. 加载 base model (Unsloth FastLanguageModel.from_pretrained)
    #   2. 如果 args.lora 给了: model.load_adapter(args.lora)
    #   3. 加载 τ-bench 测试任务 (前 args.num_tasks 个)
    #   4. for task in tasks:
    #          跑 model 应对 user_simulator, env.evaluate() 判断成功
    #   5. 准确率 = 成功数 / 总数
    #   6. 把 {"setup": "baseline" or "sft", "accuracy": X, "details": [...]} 存到 args.out
    #   7. 打印准确率

    setup = "baseline (no LoRA)" if args.lora is None else f"with LoRA from {args.lora}"
    print(f"[骨架] 在 τ-{args.bench} 上跑 {args.num_tasks} 个任务")
    print(f"[骨架]   模型:    {args.model}")
    print(f"[骨架]   配置:    {setup}")
    print(f"[骨架]   保存到:  {args.out}")
    print("[骨架] Week 1-2 实现具体逻辑")


if __name__ == "__main__":
    main()
