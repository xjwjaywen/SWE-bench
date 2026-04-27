"""
train.py — SFT 训练 Qwen2.5-7B + LoRA on MATH

干啥的:
    读 data_prep.py 生成的 jsonl, 用 Unsloth + TRL 微调 Qwen2.5-7B,
    只训 LoRA 补丁 (~1600 万参数), 不动 base 模型 (70 亿参数).
    训完保存 LoRA 文件 (~50MB) 到 outputs/.

输入:  data/sft_train.jsonl
输出:  outputs/v01_sft/   (LoRA adapter + tokenizer)

什么时候跑:
    Week 2 Day 4-5, 在 L20 服务器上跑.
    单卡 4-8 小时, 多卡更快但本阶段单卡就够.

依赖 (服务器):
    pip install torch unsloth trl bitsandbytes peft accelerate

跑法 (强烈建议指定 GPU 避开别人):
    CUDA_VISIBLE_DEVICES=2 python -m src.train --data data/sft_train.jsonl --out outputs/v01_sft

预期看到:
    loss 数字从 ~1.5 一路降到 ~0.6 左右, 这就是训练成功的标志.
    显存占用 ~16-20 GB (L20 48GB 够).
"""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True,
                        help="SFT 数据 jsonl 文件 (来自 data_prep.py)")
    parser.add_argument("--out", type=Path, required=True,
                        help="输出目录, 训完的 LoRA 存这里")
    parser.add_argument("--model", default="unsloth/Qwen2.5-7B-Instruct",
                        help="base 模型, Unsloth 版自带 4-bit 量化")
    parser.add_argument("--epochs", type=int, default=3,
                        help="数据过几遍, MATH 这种数学题 3 epoch 比较稳")
    parser.add_argument("--lr", type=float, default=2e-4,
                        help="学习率, LoRA 用 1e-4 ~ 5e-4 都行")
    parser.add_argument("--lora_r", type=int, default=16,
                        help="LoRA 补丁宽度, 越大越能学但越慢")
    parser.add_argument("--max_seq_length", type=int, default=2048,
                        help="单条数据最长 token 数, MATH 解答有时很长可调到 4096")
    parser.add_argument("--batch_size", type=int, default=2,
                        help="一次喂几条, L20 + 7B 大概 2-4")
    parser.add_argument("--grad_accum", type=int, default=8,
                        help="梯度累积, 等效 batch_size = batch_size * grad_accum")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    # TODO Week 2 Day 4-5:
    #   1. from unsloth import FastLanguageModel
    #      model, tokenizer = FastLanguageModel.from_pretrained(
    #          args.model, max_seq_length=args.max_seq_length, load_in_4bit=True)
    #   2. model = FastLanguageModel.get_peft_model(
    #          model, r=args.lora_r,
    #          target_modules=["q_proj","k_proj","v_proj","o_proj",
    #                          "gate_proj","up_proj","down_proj"])
    #   3. from datasets import load_dataset
    #      dataset = load_dataset("json", data_files=str(args.data), split="train")
    #   4. # 用 tokenizer 把 messages 应用 chat template, 转成训练用的 text
    #      def format_fn(ex):
    #          ex["text"] = tokenizer.apply_chat_template(ex["messages"], tokenize=False)
    #          return ex
    #      dataset = dataset.map(format_fn)
    #   5. from trl import SFTTrainer, SFTConfig
    #      trainer = SFTTrainer(
    #          model=model, train_dataset=dataset,
    #          args=SFTConfig(
    #              output_dir=str(args.out),
    #              num_train_epochs=args.epochs,
    #              learning_rate=args.lr,
    #              per_device_train_batch_size=args.batch_size,
    #              gradient_accumulation_steps=args.grad_accum,
    #              logging_steps=10,
    #              save_strategy="epoch",
    #              # response_template="<|im_start|>assistant",  # 让 loss 只算 assistant 部分
    #          ))
    #   6. trainer.train()
    #   7. model.save_pretrained(str(args.out))
    #      tokenizer.save_pretrained(str(args.out))

    print(f"[骨架] 训练 {args.model}")
    print(f"[骨架]   数据:        {args.data}")
    print(f"[骨架]   输出:        {args.out}")
    print(f"[骨架]   epochs:      {args.epochs}")
    print(f"[骨架]   lr:          {args.lr}")
    print(f"[骨架]   lora_r:      {args.lora_r}")
    print(f"[骨架]   batch:       {args.batch_size} × grad_accum={args.grad_accum} = {args.batch_size * args.grad_accum} eff")
    print("[骨架] Week 2 Day 4-5 实现具体逻辑")


if __name__ == "__main__":
    main()
