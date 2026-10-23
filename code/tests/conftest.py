import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOY_PACK = ROOT / "packs" / "toy" / "toy_pack.yaml"

HYPS = {
    "nda-2": "Confidential Information shall only include technical information.",
    "nda-3": "Confidential Information may include verbally conveyed information.",
    "nda-4": "Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in Agreement.",
    "nda-8": "Receiving Party shall notify Disclosing Party in case Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information.",
    "nda-10": "Receiving Party shall not disclose the fact that Agreement was agreed or negotiated.",
    "nda-11": "Receiving Party shall not reverse engineer any objects which embody Disclosing Party's Confidential Information.",
    "nda-15": "Agreement shall not grant Receiving Party any right to Confidential Information.",
    "nda-16": "Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement.",
    "nda-18": "Receiving Party shall not solicit some of Disclosing Party's representatives.",
    "nda-19": "Some obligations of Agreement may survive termination of Agreement.",
}

DOC_A = [
    "MUTUAL NON-DISCLOSURE AGREEMENT",
    "Confidential Information means any information disclosed in writing or orally by either party.",
    "The Recipient shall use Confidential Information solely for the purpose of evaluating the proposed transaction.",
    "Upon termination, the Recipient shall promptly return or destroy all Confidential Information.",
    "The obligations in this Agreement shall survive termination for a period of three (3) years.",
    "This Agreement shall be governed by the laws of the State of Delaware.",
]
# Doc B omits return, oral disclosure and survival; it has a non-solicit and Singapore law.
DOC_B = [
    "CONFIDENTIALITY AGREEMENT",
    "Confidential Information means technical data delivered in written form and marked confidential.",
    "The Recipient shall use Confidential Information solely for the purpose of the evaluation.",
    "For twelve (12) months neither party shall solicit or hire any employee of the other party.",
    "This Agreement shall be governed by the laws of Singapore.",
]

LABELS_A = {"nda-3": ("Entailment", [1]), "nda-4": ("Entailment", [2]), "nda-16": ("Entailment", [3]),
            "nda-19": ("Entailment", [4])}
LABELS_B = {"nda-4": ("Entailment", [2]), "nda-18": ("Entailment", [3])}


def _doc(i, segs, labels):
    text, spans, pos = "", [], 0
    for s in segs:
        spans.append([pos, pos + len(s)])
        text += s + "\n"
        pos += len(s) + 1
    anns = {h: {"choice": labels.get(h, ("NotMentioned", []))[0], "spans": labels.get(h, ("", []))[1]}
            for h in HYPS}
    return {"id": i, "file_name": f"doc{i}.txt", "text": text, "spans": spans,
            "annotation_sets": [{"annotations": anns}], "document_type": "test", "url": ""}


@pytest.fixture(scope="session")
def cnli_dir(tmp_path_factory) -> Path:
    d = tmp_path_factory.mktemp("cnli") / "contract-nli"
    d.mkdir()
    payload = {"documents": [_doc(1, DOC_A, LABELS_A), _doc(2, DOC_B, LABELS_B)],
               "labels": {h: {"short_description": h, "hypothesis": t} for h, t in HYPS.items()}}
    for split in ("train", "dev", "test"):
        (d / f"{split}.json").write_text(json.dumps(payload))
    return d


KEYWORDS = {  # crude "oracle" used by the fake backend: term keyword -> segment regex
    "return or destroy": r"return or destroy",
    "orally": r"orally",
    "verbally": r"orally",
    "destroy or return": r"return or destroy",
    "survive": r"survive",
    "notify": r"notify",
    "other than the stated purpose": r"solely for the purpose",
    "reverse engineer": r"reverse engineer",
    "solicit": r"solicit",
    "existence": r"existence",
    "licence": r"licen[cs]e",
    "technical information only": r"technical data",
}


def oracle_responder(req):
    """Fake LLM: answers check prompts by keyword lookup, field prompts by regex."""
    msg = req.messages[-1].content
    if msg.startswith("QUESTION:"):
        segs = re.findall(r"^\[(\d+)\] (.*)$", msg, re.M)
        if "governs" in msg:
            for i, s in segs:
                m = re.search(r"laws of (?:the State of )?(\w+)", s)
                if m:
                    return json.dumps({"value": m.group(1).lower(), "evidence": [int(i)]})
        if "How long do the confidentiality" in msg:
            for i, s in segs:
                if "three (3) years" in s:
                    return json.dumps({"value": 36, "evidence": [int(i)]})
        return json.dumps({"value": None, "evidence": []})
    stmt = re.search(r"STATEMENT: (.*)", msg).group(1)
    segs = re.findall(r"^\[(\d+)\] (.*)$", msg, re.M)
    for key, pat in KEYWORDS.items():
        if key in stmt:
            ev = [int(i) for i, s in segs if re.search(pat, s, re.I)]
            if ev:
                return json.dumps({"rationale": "found", "label": "Entailment", "evidence": ev, "confidence": 0.9})
    return json.dumps({"rationale": "absent", "label": "NotMentioned", "evidence": [], "confidence": 0.8})
