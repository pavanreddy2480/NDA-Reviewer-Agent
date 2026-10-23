"""Download ContractNLI into data/raw/.

The official link (stanfordnlp.github.io) serves the same zip as the repository's gh-pages
branch on GitHub; we try the GitHub copy first because some networks block github.io.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import httpx

URLS = (
    "https://raw.githubusercontent.com/stanfordnlp/contract-nli/gh-pages/resources/contract-nli.zip",
    "https://stanfordnlp.github.io/contract-nli/resources/contract-nli.zip",
)
KEEP = ("train.json", "dev.json", "test.json", "README.md", "LICENSE", "TERMS")


def download_contractnli(dest: str | Path = "data/raw") -> Path:
    dest = Path(dest)
    target = dest / "contract-nli"
    if all((target / f).exists() for f in ("train.json", "dev.json", "test.json")):
        return target
    last_err: Exception | None = None
    for url in URLS:
        try:
            r = httpx.get(url, follow_redirects=True, timeout=120)
            r.raise_for_status()
            break
        except Exception as e:  # try the next mirror
            last_err = e
    else:
        raise RuntimeError(f"could not download ContractNLI: {last_err}")
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for name in z.namelist():
            base = name.rsplit("/", 1)[-1]
            if name.count("/") == 1 and base in KEEP:  # skip raw/ PDFs
                (target / base).write_bytes(z.read(name))
    return target
