"""A small synthetic stand-in for ContractNLI, for offline end-to-end runs (`cc smoke`) and tests.

Each NDA is assembled from a clause bank: for every ContractNLI hypothesis the NDA states it
(Entailment), states the opposite (Contradiction, where the bank has wording for that) or leaves
it out (NotMentioned), and the annotation is written from that choice with the clause's span as
evidence, exactly in ContractNLI's format. Field facts (term length, governing law, return
deadline, personal data, mutual) are drawn too and written as *verified* labels in the
`benchmark/labels.py` format, so field rules are scored as well.

The clause wording is ours, written to read like ordinary NDA text. It is only for checking that
the code runs end to end on a known ground truth: no result in the report comes from it.
"""

from __future__ import annotations

import random

from ..data.contractnli import Annotation, ContractNLI, Hypothesis, NDADocument, NLILabel

HYPOTHESES = {
    "nda-1": ("Explicit identification", "All Confidential Information shall be expressly identified by the Disclosing Party."),
    "nda-2": ("None-inclusion of non-technical information", "Confidential Information shall only include technical information."),
    "nda-3": ("Inclusion of verbally conveyed information", "Confidential Information may include verbally conveyed information."),
    "nda-4": ("Limited use", "Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in Agreement."),
    "nda-5": ("Sharing with employees", "Receiving Party may share some Confidential Information with some of Receiving Party's employees."),
    "nda-7": ("Sharing with third-parties", "Receiving Party may share some Confidential Information with some third-parties (including consultants, agents and professional advisors)."),
    "nda-8": ("Notice on compelled disclosure", "Receiving Party shall notify Disclosing Party in case Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information."),
    "nda-10": ("Confidentiality of Agreement", "Receiving Party shall not disclose the fact that Agreement was agreed or negotiated."),
    "nda-11": ("No reverse engineering", "Receiving Party shall not reverse engineer any objects which embody Disclosing Party's Confidential Information."),
    "nda-12": ("Permissible development of similar information", "Receiving Party may independently develop information similar to Confidential Information."),
    "nda-13": ("Permissible acquirement of similar information", "Receiving Party may acquire information similar to Confidential Information from a third party."),
    "nda-15": ("No licensing", "Agreement shall not grant Receiving Party any right to Confidential Information."),
    "nda-16": ("Return of confidential information", "Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement."),
    "nda-17": ("Permissible copy", "Receiving Party may create a copy of some Confidential Information in some circumstances."),
    "nda-18": ("No solicitation", "Receiving Party shall not solicit some of Disclosing Party's representatives."),
    "nda-19": ("Survival of obligations", "Some obligations of Agreement may survive termination of Agreement."),
    "nda-20": ("Permissible post-agreement possession", "Receiving Party may retain some Confidential Information even after the return or destruction of Confidential Information."),
}

# hypothesis -> (entailing clause, contradicting clause or None)
BANK = {
    "nda-1": ("Confidential Information must be marked as confidential at the time of disclosure, or identified as confidential in writing within thirty days.",
              "Information is Confidential Information whether or not it is marked or identified as confidential."),
    "nda-2": ("For the avoidance of doubt, Confidential Information shall be limited to technical information, including specifications and source code, and shall not include business information.",
              "Confidential Information includes technical, business, financial and commercial information of every kind."),
    "nda-3": ("Confidential Information includes information disclosed orally, visually or in writing.",
              "Oral disclosures are not Confidential Information unless reduced to writing within ten days."),
    "nda-4": ("The Receiving Party shall use Confidential Information solely for the purpose of evaluating the proposed business relationship and for no other purpose.", None),
    "nda-5": ("The Receiving Party may disclose Confidential Information to its employees who need to know it for the purpose and who are bound by confidentiality obligations.", None),
    "nda-7": ("The Receiving Party may disclose Confidential Information to its professional advisers, consultants and agents who are bound by duties of confidence.", None),
    "nda-8": ("If the Receiving Party is required by law, regulation or court order to disclose Confidential Information, it shall promptly notify the Disclosing Party so that it may seek a protective order.", None),
    "nda-10": ("Neither party shall disclose the existence or terms of this Agreement or the fact that discussions are taking place.", None),
    "nda-11": ("The Receiving Party shall not reverse engineer, decompile or disassemble any prototype, software or other object that embodies Confidential Information.", None),
    "nda-12": ("Nothing in this Agreement prevents the Receiving Party from independently developing information similar to the Confidential Information without use of it.", None),
    "nda-13": ("Obligations do not apply to information the Receiving Party lawfully receives from a third party without a duty of confidence.", None),
    "nda-15": ("No licence or other right in the Confidential Information is granted to the Receiving Party under this Agreement.", None),
    "nda-16": ("On termination or on written request, the Receiving Party shall return or destroy all Confidential Information and all copies within {return_days} days.", None),
    "nda-17": ("The Receiving Party may make such copies of Confidential Information as are reasonably necessary for the purpose.", None),
    "nda-18": ("For twelve (12) months after the date of this Agreement, neither party shall solicit for employment any employee of the other party with whom it had contact.", None),
    "nda-19": ("The obligations of confidentiality in this Agreement survive any termination or expiry of this Agreement.", None),
    "nda-20": ("The Receiving Party may retain one archival copy of Confidential Information for legal compliance purposes after return or destruction.", None),
}

STATES = ["Delaware", "New York", "California", "Texas", "Massachusetts"]
COUNTRIES = ["England and Wales", "Singapore"]


def synthetic_nda(doc_id: int, rng: random.Random, split: str) -> tuple[NDADocument, dict]:
    mutual = rng.random() < 0.5
    years = rng.choice([2, 3, 5])
    word = {2: "two", 3: "three", 5: "five"}[years]
    return_days = rng.choice([10, 30, 60])
    law = rng.choice(STATES + STATES + COUNTRIES)
    pd = rng.random() < 0.4
    spans_text = [
        f"{'MUTUAL ' if mutual else ''}NON-DISCLOSURE AGREEMENT",
        f'This Agreement is made between Acme Corp ("Company") and Counterparty LLC ("Recipient")'
        f"{' and each party may disclose information to the other' if mutual else ''}.",
        "1. Definitions. \"Confidential Information\" means non-public information disclosed by one party to the other.",
    ]
    if pd:
        spans_text.append("Confidential Information may include personal data of customers and employees, which the Recipient shall process only on documented instructions.")
    annotations = {}
    for h, (ent, con) in BANK.items():
        r = rng.random()
        if r < 0.6:
            text, label = ent.format(return_days=return_days), NLILabel.ENTAILMENT
        elif con and r < 0.75:
            text, label = con, NLILabel.CONTRADICTION
        else:
            annotations[h] = Annotation(NLILabel.NOT_MENTIONED, ())
            continue
        annotations[h] = Annotation(label, (len(spans_text),))
        spans_text.append(f"{len(spans_text)}. {text}" if rng.random() < 0.3 else text)
    term_seg = len(spans_text)
    spans_text.append(f"The obligations of confidentiality under this Agreement last for {word} ({years}) years from the date of disclosure.")
    spans_text.append(f"This Agreement shall be governed by the laws of the State of {law}." if law in STATES
                      else f"This Agreement shall be governed by the laws of {law}.")
    spans_text.append("Each party acknowledges that a breach may cause irreparable harm and that injunctive relief may be sought.")
    text, spans, pos = "", [], 0
    for t in spans_text:
        spans.append((len(text), len(text) + len(t)))
        text += t + "\n"
    doc = NDADocument(doc_id, f"synthetic-{doc_id}.txt", text, spans, annotations, "synthetic", "", split)
    has_return = annotations["nda-16"].label == NLILabel.ENTAILMENT
    labels = {
        "verified": True, "synthetic": True, "is_template": False, "mutual": mutual, "company_party": "Acme Corp",
        "governing_law": law.lower() if law in STATES else ("united kingdom" if law.startswith("England") else law.lower()),
        "personal_data": pd, "counterparty_kind": "company", "counterparty_role": "unknown", "counterparty_country": None,
        "fields": {"confidentiality_term_months": float(years * 12), "return_deadline_days": float(return_days) if has_return else None,
                   "non_solicit_months": 12.0 if annotations["nda-18"].label == NLILabel.ENTAILMENT else None,
                   "non_compete": False, "survival_months": None, "dispute_forum": None},
        "terms": {},
        "_term_segment": term_seg,
    }
    return doc, labels


def synthetic_contractnli(n_per_split: dict[str, int] | None = None, seed: int = 0) -> tuple[ContractNLI, dict[int, dict]]:
    n_per_split = n_per_split or {"train": 8, "dev": 6, "test": 12}
    rng = random.Random(f"synthetic-{seed}")
    hyps = {k: Hypothesis(k, s, t) for k, (s, t) in HYPOTHESES.items()}
    splits, labels, next_id = {}, {}, 1
    for split, n in n_per_split.items():
        docs = []
        for _ in range(n):
            d, lab = synthetic_nda(next_id, rng, split)
            lab.pop("_term_segment", None)
            docs.append(d)
            labels[d.id] = lab
            next_id += 1
        splits[split] = docs
    return ContractNLI(hyps, splits), labels


def write_synthetic(root, seed: int = 0, n_per_split: dict[str, int] | None = None) -> dict:
    """Write the synthetic set in ContractNLI's JSON layout (train/dev/test.json) plus labels.yaml."""
    import json
    from pathlib import Path

    import yaml

    data, labels = synthetic_contractnli(n_per_split, seed)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for split, docs in data.splits.items():
        raw = {"labels": {k: {"short_description": h.short_description, "hypothesis": h.text}
                          for k, h in data.hypotheses.items()},
               "documents": [{"id": d.id, "file_name": d.file_name, "text": d.text, "spans": [list(s) for s in d.spans],
                              "document_type": d.document_type, "url": "",
                              "annotation_sets": [{"annotations": {h: {"choice": a.label.value, "spans": list(a.spans)}
                                                                   for h, a in d.annotations.items()}}]}
                             for d in docs]}
        (root / f"{split}.json").write_text(json.dumps(raw))
    (root / "labels.yaml").write_text(yaml.safe_dump({k: v for k, v in labels.items()}, sort_keys=True))
    return {"root": str(root), "n": {s: len(v) for s, v in data.splits.items()}}
