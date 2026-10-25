"""Ground truth per NDA (design §7.1, §7.2).

- Rules anchored to a ContractNLI hypothesis get each NDA's real status from the expert
  labels: for a `require` rule, NotMentioned is a natural omission and Contradiction a
  natural violation; for a `forbid` rule, Entailment is a violation.
- Field rules use the NDA labels (benchmark/labels.py; governing law is the top-level label,
  "none" = the NDA names no governing law). A value left blank in a template, a value the two
  labelling models disputed, or an "unknown" governing law is unscored, never an omission.
- Unanchored require/forbid rules (most law-pack provisions and the pack's "other" rules) use
  the `terms` labels: whether the NDA contains the rule's term (autolabel.py). Without a label
  they are unscored.
- Applicability uses the *gold* deal: facts left blank on the form are taken from the labels.
  If a fact is still unknown and changes whether a rule applies, the rule is unscored.
- Planted defects (benchmark/planter.py) are added on top. A status that comes from a planted
  override counts as planted, not natural. Rules whose evidence the planter touched without
  re-deriving their status are unscored (review problem 7). A planted defect on a rule that
  does not apply (or may not) under the gold deal is dropped, so planting and scoring agree.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..data.contractnli import NDADocument, NLILabel
from ..policy.jurisdictions import normalise_jurisdiction
from ..policy.schema import INFERABLE_FACTS, DealContext, LawPack, PolicyPack, Rule, applicability
from ..review.fields import UNSPECIFIED
from ..review.findings import FindingType

DISPUTED = "disputed"  # the two labelling models disagreed and no person has resolved it
NO_LAW = "none"  # the NDA names no governing law
_NOT_KNOWN = ("", "unknown", "blank", DISPUTED, NO_LAW)


@dataclass(frozen=True)
class GoldDefect:
    rule_id: str
    type: FindingType
    evidence: tuple[int, ...] = ()
    origin: str = "natural"  # "natural" | "planted"

    @property
    def key(self) -> tuple[str, str]:
        return (self.rule_id, self.type.value)


@dataclass
class GoldNDA:
    doc_id: int
    deal: DealContext  # gold deal, facts filled from labels
    defects: list[GoldDefect]
    scored_rules: list[str] = field(default_factory=list)  # applicable rules with known status
    unscored_rules: list[str] = field(default_factory=list)
    not_applicable: list[str] = field(default_factory=list)  # flagging these is a false alarm


def known(v) -> bool:
    """False for None and for the placeholder strings ("unknown", "blank", "disputed", "none")."""
    return not (v is None or (isinstance(v, str) and v.strip().lower() in _NOT_KNOWN))


def finding_type(rule: Rule, violation: bool) -> FindingType:
    """The type a broken rule is reported as, shared by planter and gold."""
    if rule.id.startswith("LAW-"):
        return FindingType.STATUTORY_RISK
    if not violation:
        return FindingType.OMISSION
    return FindingType.APPROVAL_NEEDED if rule.approval else FindingType.VIOLATION


def anchored_status(rule: Rule, label: NLILabel, spans: tuple[int, ...], origin: str = "natural") -> GoldDefect | None:
    if rule.kind == "require" and label == NLILabel.CONTRADICTION:
        t = finding_type(rule, True)
    elif rule.kind == "require" and label == NLILabel.NOT_MENTIONED:
        t = finding_type(rule, False)
    elif rule.kind == "forbid" and label == NLILabel.ENTAILMENT:
        t = finding_type(rule, True)
    else:
        return None
    return GoldDefect(rule.id, t, spans if t != FindingType.OMISSION else (), origin)


def gold_deal(deal: DealContext, labels: dict | None) -> DealContext:
    """Fill facts left blank on the form from the labels. Placeholders mean unknown."""
    upd = {}
    for f in INFERABLE_FACTS:
        v = getattr(deal, f)
        if not known(v):
            lab = (labels or {}).get(f)
            if f == "governing_law" and known(lab):
                lab = normalise_jurisdiction(str(lab))
            upd[f] = lab if known(lab) else None
        elif f == "governing_law":
            upd[f] = normalise_jurisdiction(str(v))
    return deal.model_copy(update=upd)


def field_value(rule: Rule, labels: dict, planted: dict | None = None):
    """(known, value) of a field rule's field after planting; value None = absent from the NDA."""
    from ..review.fields import _normalise

    planted = planted or {}
    f = rule.constraint.field
    if f in planted.get("field_overrides", {}):
        return True, planted["field_overrides"][f]
    if f in planted.get("touched_fields", []):
        return False, None
    fields = labels.get("fields", {}) or {}
    if f == "governing_law":
        v = labels.get("governing_law", fields.get("governing_law"))
        if isinstance(v, str) and v.strip().lower() == NO_LAW:
            return True, None
        return (True, normalise_jurisdiction(str(v))) if known(v) else (False, None)
    if f not in fields:
        return False, None
    v = fields[f]
    if v is None:
        return True, None
    if not known(v):
        return False, None
    v = _normalise(f, v)
    return (False, None) if v == UNSPECIFIED else (True, v)


RETURN_HYPOTHESIS = "nda-16"  # "Receiving Party shall destroy or return some Confidential Information ..."


def _return_clause(doc: NDADocument, planted: dict) -> bool | None:
    """Does the (planted) NDA have a return/destroy obligation, by ContractNLI's expert label?
    None if the planter touched it without re-deriving it."""
    h = RETURN_HYPOTHESIS
    if h in planted.get("overrides", {}):
        return planted["overrides"][h][0] != NLILabel.NOT_MENTIONED.value
    if h in set(planted.get("touched_hypotheses", [])) or h not in doc.annotations:
        return None
    return doc.annotations[h].label != NLILabel.NOT_MENTIONED


def gold_for(doc: NDADocument, deal: DealContext, pack: PolicyPack, labels: dict | None = None,
             law_pack: LawPack | None = None, planted: dict | None = None) -> GoldNDA:
    """`labels`: this NDA's label entry. `planted`: this NDA's planter manifest entry
    (PlantedNDA.gold_entry(): defects, touched hypotheses and fields, overrides, label updates)."""
    planted = planted or {}
    labels = {**(labels or {}), **planted.get("label_updates", {})}
    gdeal = gold_deal(deal, labels)
    g = GoldNDA(doc.id, gdeal, [])
    touched = set(planted.get("touched_hypotheses", []))
    overrides = planted.get("overrides", {})
    index_map = planted.get("index_map")  # original span -> planted segment index
    edited = planted.get("edited", False)  # original text was deleted or replaced
    terms = labels.get("terms", {}) or {}

    def tkey(rule: Rule) -> str:  # same keys as autolabel.term_key
        return rule.id if rule.id.startswith("LAW-") else f"{pack.company}:{rule.id}"

    rules = list(pack.rules) + (law_pack.as_rules() if law_pack else [])
    app = {r.id: applicability(r, gdeal) for r in rules}
    planted_defects = [d for d in planted.get("defects", []) if app.get(d.rule_id) is True]
    planted_rules = {d.rule_id for d in planted.get("defects", [])}
    for rule in rules:
        if app[rule.id] is False:
            g.not_applicable.append(rule.id)
            continue
        if app[rule.id] is None:
            g.unscored_rules.append(rule.id)
            continue
        if rule.id in planted_rules:
            g.scored_rules.append(rule.id)
            continue
        d: GoldDefect | None
        if rule.anchor is not None:
            h = rule.anchor.hypothesis
            if h in overrides:
                lab, spans = overrides[h]
                d = anchored_status(rule, NLILabel(lab), tuple(spans), origin="planted")
            elif h in touched:
                g.unscored_rules.append(rule.id)
                continue
            else:
                a = doc.annotations[h]
                spans = a.spans if index_map is None else tuple(index_map[x] for x in a.spans if x in index_map)
                d = anchored_status(rule, a.label, spans)
        elif rule.kind == "field":
            ok, value = field_value(rule, labels, planted)
            if not ok:
                g.unscored_rules.append(rule.id)
                continue
            origin = "planted" if rule.constraint.field in planted.get("field_overrides", {}) else "natural"
            if value is None and rule.constraint.field == "return_deadline_days" and _return_clause(doc, planted) is not False:
                # labellers answer null both for "no return clause" and for "return promptly"; the
                # expert label says which. A return clause without a number of days is unscored.
                g.unscored_rules.append(rule.id)
                continue
            if value is None and rule.constraint.check_absent():
                d = None  # no such clause meets an "at most" rule (gold-deals audit, point 1)
            elif value is None:
                d = GoldDefect(rule.id, finding_type(rule, False), (), origin)
            else:
                try:
                    good = rule.constraint.check(value)
                except TypeError:  # e.g. a text value for a numeric field
                    g.unscored_rules.append(rule.id)
                    continue
                d = None if good else GoldDefect(rule.id, finding_type(rule, True), (), origin)
        elif isinstance(terms.get(tkey(rule)), bool) and not (edited and terms[tkey(rule)]):
            # Unanchored require/forbid rule with a presence label. If the planter deleted or
            # replaced original text, a labelled-present term may be gone: unscored.
            present = terms[tkey(rule)]
            d = anchored_status(rule, NLILabel.ENTAILMENT if present else NLILabel.NOT_MENTIONED, ())
        else:
            g.unscored_rules.append(rule.id)
            continue
        g.scored_rules.append(rule.id)
        if d is not None:
            g.defects.append(d)
    g.defects.extend(planted_defects)
    return g
