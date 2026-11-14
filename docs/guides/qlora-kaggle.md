# Fine-tuning the Llama-3.1-8B adapter on Kaggle (QLoRA)

Proposal §5 and §10: one multi-task QLoRA adapter (ContractNLI on the 12 training hypotheses, CUAD
clause tags, obligation frames), two runs of about 8 GPU-hours each on a Kaggle T4. The five
held-out hypotheses (`nda-3, nda-8, nda-12, nda-16, nda-20`) never enter the training data.

## 1. Build the training mix (any machine, no GPU)

```bash
cc data download                                   # ContractNLI
# CUAD_v1.json from https://www.atticusprojectai.org/cuad (put it in data/raw/cuad/)
cc frames silver --backend gemini-flash --split train --out data/finetune/silver_frames.jsonl
cc finetune data --cuad data/raw/cuad/CUAD_v1.json --frames data/finetune/silver_frames.jsonl \
    --max-per-task 6000 --out data/finetune
```

This writes `train.jsonl`, `val.jsonl` (5%) and `manifest.json` (counts per task and the held-out
list). Upload `data/finetune/` as a Kaggle dataset.

## 2. Train (Kaggle notebook, GPU T4, internet on, `HF_TOKEN` secret set)

```python
!pip install -q "transformers>=4.44" "peft>=0.12" "trl>=0.10" "bitsandbytes>=0.43" accelerate datasets
!cp -r /kaggle/input/counselcopilot-code /kaggle/working/code && cd /kaggle/working/code && pip install -q -e .
import os
from kaggle_secrets import UserSecretsClient
os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
!cd /kaggle/working/code && python -m counselcopilot.finetune.train \
    --data /kaggle/input/counselcopilot-finetune --out /kaggle/working/qlora-llama8b --seed 0
```

Settings (in `finetune/train.py`): 4-bit NF4 with double quantisation, LoRA r=16, alpha=32,
dropout 0.05 on all attention and MLP projections, lr 2e-4 cosine, 1 epoch, 1,536-token
sequences, loss on the assistant turn only. Run a second seed (`--seed 1`) for the variance the
proposal reports. Save `/kaggle/working/qlora-llama8b` as an output dataset.

## 3. Serve the adapter and use it

```python
!nohup python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3.1-8B-Instruct --dtype half --max-model-len 8192 \
    --enable-lora --lora-modules counselcopilot=/kaggle/input/qlora-llama8b --port 8000 > vllm.log 2>&1 &
```

The backend `llama-tuned` in `configs/backends.toml` points at it (model name `counselcopilot`).

```bash
cc nli --backend llama-tuned --split test          # held-out vs training hypotheses
cc rq1 --backend llama-vllm --checker-backend llama-tuned --pack ... --split test --system pipeline
cc cascade runs/<local> runs/<remote> --pack ... --second-local runs/<tuned>   # cascade ablation
```

CUAD tag F1 on CUAD's test split is computed with `counselcopilot.finetune.data.cuad_tag_f1`.
