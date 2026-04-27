"""
eval.py — 在 MATH 测试集上评测模型

干啥的:
    加载模型 (base 或 base + LoRA), 让它解 MATH test 题目, 从输出中
    提取 \\boxed{...} 里的最终答案, 和 ground truth 比对算准确率.
    完全程序化判分, 不需要任何外部 API.

输入:  --lora 路径 (可选, 不给就跑 baseline 不带 LoRA)
输出:  控制台打印准确率 + outputs/eval_results.json (每题对错记录)

什么时候跑:
    Week 1 Day 5-7:  python -m src.eval                      → baseline ~50%
    Week 2 Day 6-7:  python -m src.eval --lora outputs/v01_sft → SFT 后, 应该 > baseline

依赖:
    pip install torch unsloth peft datasets sympy

跑法 (避开别人占用的 GPU):
    CUDA_VISIBLE_DEVICES=2 python -m src.eval --num_problems 100
    CUDA_VISIBLE_DEVICES=2 python -m src.eval --num_problems 100 --lora outputs/v01_sft
"""

import argparse
import json
import re
from pathlib import Path


SYSTEM_PROMPT = (
    "You are a math problem solver. Solve the problem step by step, "
    "showing your reasoning. Put your final answer inside \\boxed{}."
)


def extract_boxed_answer(text: str) -> str | None:
    """从模型输出里抠出 \\boxed{X} 中的 X.
    MATH 数据集的 ground truth solution 也是这种格式, 所以两边都用这个函数抠."""
    # 简单实现: 找最后一个 \boxed{...} (模型可能有多个 box, 取最后那个最终答案)
    # 注意 LaTeX 嵌套花括号问题, 这个简单版本对大部分情况够用
    matches = re.findall(r"\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", text)
    return matches[-1].strip() if matches else None


def is_equivalent(pred: str, gold: str) -> bool:
    """判断两个答案是否等价. v0.1 用最简单的字符串比对 (去空格 + 大小写).
    v0.2 升级到 sympy 表达式等价判断 (能识别 1/2 == 0.5 == 2^{-1} 这种)."""
    if pred is None or gold is None:
        return False
    return pred.replace(" ", "").lower() == gold.replace(" ", "").lower()
    # TODO v0.2: 用 sympy.simplify(parse_latex(pred) - parse_latex(gold)) == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lora", type=Path, default=None,
                        help="LoRA 文件夹路径, 不给就跑 base 模型 baseline")
    parser.add_argument("--num_problems", type=int, default=100,
                        help="评测多少题, 100 题大约 30-60 分钟, 全量 5000 题需要数小时")
    parser.add_argument("--model", default="unsloth/Qwen2.5-7B-Instruct",
                        help="base 模型")
    parser.add_argument("--out", type=Path, default=Path("outputs/eval_results.json"),
                        help="评测结果保存路径")
    parser.add_argument("--max_new_tokens", type=int, default=1024,
                        help="模型生成最长长度, MATH 解答可以很长")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="0.0 = 贪心解码, 评测时一般用 0 保证可复现")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    # TODO Week 1 Day 5-7:
    #   1. from unsloth import FastLanguageModel
    #      model, tokenizer = FastLanguageModel.from_pretrained(
    #          args.model, max_seq_length=4096, load_in_4bit=True)
    #      FastLanguageModel.for_inference(model)  # 推理模式
    #   2. if args.lora:
    #          model.load_adapter(str(args.lora))
    #   3. from datasets import load_dataset
    #      ds = load_dataset("hendrycks/competition_math", split="test")
    #      ds = ds.select(range(args.num_problems))
    #   4. results = []
    #      correct = 0
    #      for ex in tqdm(ds):
    #          prompt = tokenizer.apply_chat_template([
    #              {"role": "system", "content": SYSTEM_PROMPT},
    #              {"role": "user", "content": ex["problem"]},
    #          ], tokenize=False, add_generation_prompt=True)
    #          # 生成
    #          inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    #          out = model.generate(**inputs, max_new_tokens=args.max_new_tokens,
    #                               do_sample=False)
    #          response = tokenizer.decode(out[0][inputs.input_ids.shape[1]:],
    #                                      skip_special_tokens=True)
    #          pred = extract_boxed_answer(response)
    #          gold = extract_boxed_answer(ex["solution"])
    #          ok = is_equivalent(pred, gold)
    #          correct += int(ok)
    #          results.append({
    #              "problem": ex["problem"][:200],
    #              "pred": pred, "gold": gold, "correct": ok,
    #          })
    #   5. accuracy = correct / len(ds)
    #      with open(args.out, "w") as f:
    #          json.dump({"setup": "baseline" if not args.lora else f"lora:{args.lora}",
    #                     "accuracy": accuracy, "n": len(ds), "details": results}, f, indent=2)
    #      print(f"\\n✅ Accuracy: {accuracy:.1%} ({correct}/{len(ds)})")

    setup = "baseline (no LoRA)" if args.lora is None else f"with LoRA from {args.lora}"
    print(f"[骨架] 在 MATH test 上跑 {args.num_problems} 题")
    print(f"[骨架]   模型:    {args.model}")
    print(f"[骨架]   配置:    {setup}")
    print(f"[骨架]   保存到:  {args.out}")
    print("[骨架] Week 1 Day 5-7 实现具体逻辑")


if __name__ == "__main__":
    main()
