# Serving Llama-3.1-8B on Kaggle with vLLM

Kaggle notebook, accelerator **GPU T4 x2**, internet on. Llama 3.1 is gated: accept the licence
on Hugging Face and add your token as a Kaggle secret named `HF_TOKEN`.

```python
# cell 1: install and start the server in the background
!pip install -q vllm
import os
from kaggle_secrets import UserSecretsClient
os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
!nohup python -m vllm.entrypoints.openai.api_server \
    --model hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 \
    --dtype half --tensor-parallel-size 2 --max-model-len 16384 \
    --gpu-memory-utilization 0.90 --port 8000 > vllm.log 2>&1 &
```

```python
# cell 2: wait until it answers (takes a few minutes the first time)
!until curl -s localhost:8000/v1/models > /dev/null; do sleep 10; done; tail -3 vllm.log
```

```python
# cell 3: install the code (upload the code/ folder as a Kaggle dataset, or git clone it)
!cp -r /kaggle/input/counselcopilot-code /kaggle/working/code
%cd /kaggle/working/code
!pip install -q -e .
!cc data download
!cc nli --backend llama-vllm --split dev --workers 32
!cc rq1 --backend llama-vllm --pack packs/toy/toy_pack.yaml --split dev --preset full --workers 32
```

Notes
- T4s don't support bfloat16, hence `--dtype half`.
- vLLM batches concurrent requests, so keep `--workers` high (32-64).
- Save `data/cache/llm.sqlite` and `runs/` as notebook output; copy the cache back in next
  session so finished calls are never paid for twice (GPU hours count too).
