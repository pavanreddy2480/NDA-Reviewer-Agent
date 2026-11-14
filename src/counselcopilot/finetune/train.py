"""QLoRA training of the multi-task Llama-3.1-8B adapter (proposal §5, §10: ~16 GPU-hours on a
Kaggle T4 for two runs). Run on Kaggle, not in the test suite:

    pip install "transformers>=4.44" "peft>=0.12" "trl>=0.10" "bitsandbytes>=0.43" accelerate datasets
    python -m counselcopilot.finetune.train --data data/finetune --out runs/qlora-llama8b

Settings follow the QLoRA paper's defaults for an 8B model on 16 GB: 4-bit NF4 with double
quantisation, LoRA r=16 / alpha=32 / dropout 0.05 on all attention and MLP projections, lr 2e-4
cosine, 1 epoch, sequences cut at 1,536 tokens (the checker's prompts with 12 segments fit), and
loss on the assistant turn only. The adapter is then served by vLLM with `--enable-lora`
(docs/guides/qlora-kaggle.md) and used as the `llama-tuned` backend, both as the checker and as
the frame extractor.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class QLoRAConfig:
    base_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    r: int = 16
    alpha: int = 32
    dropout: float = 0.05
    target_modules: tuple[str, ...] = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
    lr: float = 2e-4
    epochs: float = 1.0
    max_len: int = 1536
    batch_size: int = 2
    grad_accum: int = 8
    warmup_ratio: float = 0.03
    seed: int = 0


def train(data_dir: str, out_dir: str, cfg: QLoRAConfig) -> None:  # pragma: no cover - needs a GPU
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    tok = AutoTokenizer.from_pretrained(cfg.base_model)
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model, device_map="auto", torch_dtype=torch.float16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                               bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16))
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    ds = load_dataset("json", data_files={"train": f"{data_dir}/train.jsonl", "validation": f"{data_dir}/val.jsonl"})
    lora = LoraConfig(r=cfg.r, lora_alpha=cfg.alpha, lora_dropout=cfg.dropout, task_type="CAUSAL_LM",
                      target_modules=list(cfg.target_modules))
    args = SFTConfig(output_dir=out_dir, num_train_epochs=cfg.epochs, per_device_train_batch_size=cfg.batch_size,
                     gradient_accumulation_steps=cfg.grad_accum, learning_rate=cfg.lr, lr_scheduler_type="cosine",
                     warmup_ratio=cfg.warmup_ratio, logging_steps=20, eval_strategy="steps", eval_steps=200,
                     save_steps=400, fp16=True, max_seq_length=cfg.max_len, seed=cfg.seed,
                     assistant_only_loss=True, report_to=[])
    trainer = SFTTrainer(model=model, args=args, train_dataset=ds["train"], eval_dataset=ds["validation"],
                         peft_config=lora, processing_class=tok)
    trainer.train()
    trainer.save_model(out_dir)
    Path(out_dir, "counselcopilot_qlora.json").write_text(json.dumps(asdict(cfg), indent=1))


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default="data/finetune")
    p.add_argument("--out", default="runs/qlora-llama8b")
    p.add_argument("--epochs", type=float, default=1.0)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    train(a.data, a.out, QLoRAConfig(epochs=a.epochs, lr=a.lr, seed=a.seed))


if __name__ == "__main__":  # pragma: no cover
    main()
