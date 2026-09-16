"""Lookup in any direction, plus free text search."""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional

from .model import ANCHOR, Control, Dataset

#: Prefix each framework puts in front of a bare number, so that "DORA 12" is
#: art.12 and "PCI 8.3" is req.8.3. ISO ids carry no prefix.
BARE_PREFIX = {"DORA": ("art.",), "NIS2": ("cir.", "art."), "PCI": ("req.",), "SOX": ("sec.",)}


def normalise(text: str) -> str:
    """Fold case and accents so that 'criptografia' finds 'criptografía'."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def resolve(dataset: Dataset, reference: str) -> Optional[Control]:
    """Find a control from a reference such as 'ISO 8.15', 'op.exp.8', 'req.8.3' or 'acc.1'.

    The framework prefix is optional when the identifier is unambiguous, which
    is the case for every catalogue: ENS, NIS2, DORA, PCI DSS and the SOX
    catalogue all carry a textual prefix ('op.', 'cir.', 'art.', 'req.',
    'acc.'...), so a bare number such as '8.3' is always the ISO control. To
    reach PCI DSS requirement 8.3 write 'req.8.3' or 'PCI 8.3'.
    """
    reference = (reference or "").strip()
    if not reference:
        return None
    names = "|".join(re.escape(f) for f in dataset.framework_ids)
    match = re.match(rf"^({names})[\s:.\-]+(.+)$", reference, re.IGNORECASE)
    if match:
        framework, control_id = match.group(1).upper(), match.group(2).strip()
        found = dataset.control(framework, control_id)
        if found:
            return found
        candidates = [control_id.lstrip("Aa.")]
        candidates += [prefix + control_id for prefix in BARE_PREFIX.get(framework, ())]
        for candidate in candidates:
            found = dataset.control(framework, candidate)
            if found:
                return found
        return None
    for framework in dataset.framework_ids:
        found = dataset.control(framework, reference)
        if found:
            return found
    for framework, prefixes in BARE_PREFIX.items():
        for prefix in prefixes:
            found = dataset.control(framework, prefix + reference)
            if found:
                return found
    return None


def equivalents(dataset: Dataset, control: Control) -> Dict[str, List[Dict[str, Any]]]:
    """Everything that corresponds to ``control``, whichever framework it is in.

    From an ISO control the answer is direct. From any other framework it is the
    set of ISO controls that point at it, and then, through those, the items of
    the remaining frameworks — which is how a question like "what does DORA
    article 12 mean for my ENS system?" gets answered.

    Each entry carries the coverage, the source and, when the coverage is
    partial, the rationale that says why.
    """
    if control.framework == ANCHOR:
        iso_ids = [control.id]
    else:
        iso_ids = sorted({l.iso for l in dataset.reverse.get(f"{control.framework}:{control.id}", [])},
                         key=_iso_sort_key)

    out: Dict[str, List[Dict[str, Any]]] = {fw: [] for fw in dataset.framework_ids}
    for iso_id in iso_ids:
        iso_control = dataset.control(ANCHOR, iso_id)
        if iso_control and control.framework != ANCHOR:
            link = _link_of(dataset, iso_id, control)
            out[ANCHOR].append({"control": iso_control,
                                "coverage": link.coverage if link else "none",
                                "source": link.source if link else "",
                                "rationale": link.rationale if link else {},
                                "detail": link.detail if link else {}})
        for framework, links in dataset.forward.get(iso_id, {}).items():
            if framework == control.framework and control.framework != ANCHOR:
                continue
            for link in links:
                target = dataset.control(framework, link.target)
                if target and not any(e["control"].id == target.id for e in out[framework]):
                    out[framework].append({"control": target, "coverage": link.coverage,
                                           "source": link.source, "rationale": link.rationale,
                                           "detail": link.detail, "via": iso_id})
    return out


def _link_of(dataset: Dataset, iso_id: str, control: Control):
    for link in dataset.reverse.get(f"{control.framework}:{control.id}", []):
        if link.iso == iso_id:
            return link
    return None


def _iso_sort_key(iso_id: str):
    parts = iso_id.split(".")
    return (int(parts[0]), int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0)


def search(dataset: Dataset, text: str, lang: str = "es") -> List[Control]:
    """Free text search across every catalogue, accent and case insensitive.

    Titles, family titles and — for ISO — the one-sentence summaries are
    searched, so 'backup' also finds 5.30 and 'MFA' finds PCI 8.4.
    """
    needle = normalise(text)
    if not needle:
        return []
    found: List[Control] = []
    for framework in dataset.framework_ids:
        for control in dataset.all_controls(framework):
            haystack = normalise(" ".join([
                control.id, control.title.get("en", ""), control.title.get("es", ""),
                control.summary.get("en", ""), control.summary.get("es", ""),
            ]))
            if needle in haystack:
                found.append(control)
    return found


def orphans(dataset: Dataset, framework: str) -> List[Control]:
    """Items of a framework that no ISO control maps to.

    This is the interesting half of the answer: what each regime asks for that
    an ISO 27001 certificate does not already give you.
    """
    mapped = {l.target for l in dataset.links if l.framework == framework}
    return [c for c in dataset.all_controls(framework) if c.id not in mapped]
