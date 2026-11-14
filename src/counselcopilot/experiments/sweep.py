"""Policy-corpus size sweep (proposal §4 RAG design; design §4).

Long context (B1) is compared with the full system as the policy pack grows from ~40k to ~150k
tokens (400k as a stretch). Each company's prose is padded with other policy text (real public
policies placed in `padding_dir`, or the other PolicyNDA companies' documents, renamed, as a
fallback) to the target size; the rule base is recompiled from the padded prose at every size,
because a bigger corpus also makes compilation harder. Padding documents carry no NDA rules, so
gold does not change.
"""

from __future__ import annotations

import random
import re
import shutil
from pathlib import Path

from ..baselines.common import load_policy_docs


def approx_tokens(text: str) -> int:
    return int(len(text.split()) * 1.35)


def pad_policies(policy_dir: str | Path, out_dir: str | Path, target_tokens: int,
                 padding_dirs: list[str | Path], seed: int = 0, company_name: str | None = None) -> dict:
    """Copy `policy_dir` to `out_dir` and add padding documents until the corpus reaches
    `target_tokens`. Other companies' names in padding text are replaced by `company_name` so the
    padding reads as this company's own policy."""
    src, out = Path(policy_dir), Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out)
    total = sum(approx_tokens(t) for _, t in load_policy_docs(out))
    pads = [p for d in padding_dirs for p in sorted(Path(d).glob("*.md")) if Path(d).resolve() != src.resolve()]
    rng = random.Random(f"pad-{seed}")
    rng.shuffle(pads)
    added = []
    k = 0
    while total < target_tokens and pads:
        p = pads[k % len(pads)]
        k += 1
        text = p.read_text(encoding="utf-8")
        if company_name:
            text = re.sub(r"\*\*Company:\*\*.*", f"**Company:** {company_name}", text)
        name = f"zz_padding_{k:03d}_{p.stem}.md"
        (out / name).write_text(text, encoding="utf-8")
        total += approx_tokens(text)
        added.append(name)
        if k > 10 * len(pads):
            break
    return {"out_dir": str(out), "tokens": total, "padding_docs": added}


SIZES = (40_000, 150_000, 400_000)


def sweep_plan(companies: dict[str, str | Path], out_root: str | Path, sizes=SIZES[:2],
               padding_dirs: list[str | Path] | None = None) -> list[dict]:
    """Padded corpora for every company and size. The runner then compiles each (cc compile) and
    runs B1 and Full on the 40-NDA subset (cc rq1 --system b1 / --system pipeline)."""
    out = []
    padding_dirs = padding_dirs or [str(d) for d in companies.values()]
    for company, d in companies.items():
        for size in sizes:
            info = pad_policies(d, Path(out_root) / f"{Path(d).parent.name}-{size // 1000}k", size,
                                padding_dirs, company_name=company)
            out.append({"company": company, "size": size, **info})
    return out
