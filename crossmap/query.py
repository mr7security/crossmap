"""Lookup in any direction, plus free text search."""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional

from .model import Control, Dataset, Link


def normalise(text: str) -> str:
    """Fold case and accents so that 'criptografia' finds 'criptografía'."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def resolve(dataset: Dataset, reference: str) -> Optional[Control]:
    """Find a control from a reference such as 'ISO 8.15', 'op.exp.8' or 'cir.3.2'.

    The framework prefix is optional when the identifier is unambiguous, which
    it almost always is: only ISO and DORA share a numeric shape, and DORA ids
    are prefixed with 'art.'.
    """
    reference = (reference or "").strip()
    if not reference:
        return None
    match = re.match(r"^(iso|ens|nis2|dora)[\s:.\-]+(.+)$", reference, re.IGNORECASE)
    if match:
        framework, control_id = match.group(1).upper(), match.group(2).strip()
        found = dataset.control(framework, control_id)
        if found:
            return found
        # tolerate 'DORA 9' for 'art.9' and 'ISO A.8.15' for '8.15'
        for candidate in (f"art.{control_id}", control_id.lstrip("Aa."), f"cir.{control_id}"):
            found = dataset.control(framework, candidate)
            if found:
                return found
        return None
    for framework in ("ISO", "ENS", "NIS2", "DORA"):
        found = dataset.control(framework, reference)
        if found:
            return found
    for framework, prefix in (("DORA", "art."), ("NIS2", "cir."), ("NIS2", "art.")):
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
    """
    if control.framework == "ISO":
        iso_ids = [control.id]
    else:
        iso_ids = sorted({l.iso for l in dataset.reverse.get(f"{control.framework}:{control.id}", [])},
                         key=_iso_sort_key)

    out: Dict[str, List[Dict[str, Any]]] = {"ISO": [], "ENS": [], "NIS2": [], "DORA": []}
    for iso_id in iso_ids:
        iso_control = dataset.control("ISO", iso_id)
        if iso_control and control.framework != "ISO":
            out["ISO"].append({"control": iso_control,
                               "coverage": _coverage_of(dataset, iso_id, control),
                               "source": _source_of(dataset, iso_id, control)})
        for framework, links in dataset.forward.get(iso_id, {}).items():
            if framework == control.framework and control.framework != "ISO":
                continue
            for link in links:
                target = dataset.control(framework, link.target)
                if target and not any(e["control"].id == target.id for e in out[framework]):
                    out[framework].append({"control": target, "coverage": link.coverage,
                                           "source": link.source})
    return out


def _coverage_of(dataset: Dataset, iso_id: str, control: Control) -> str:
    for link in dataset.reverse.get(f"{control.framework}:{control.id}", []):
        if link.iso == iso_id:
            return link.coverage
    return "none"


def _source_of(dataset: Dataset, iso_id: str, control: Control) -> str:
    for link in dataset.reverse.get(f"{control.framework}:{control.id}", []):
        if link.iso == iso_id:
            return link.source
    return ""


def _iso_sort_key(iso_id: str):
    parts = iso_id.split(".")
    return (int(parts[0]), int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0)


def search(dataset: Dataset, text: str, lang: str = "es") -> List[Control]:
    """Free text search across the four catalogues, accent and case insensitive."""
    needle = normalise(text)
    if not needle:
        return []
    found: List[Control] = []
    for framework in ("ISO", "ENS", "NIS2", "DORA"):
        for control in dataset.all_controls(framework):
            haystack = normalise(
                control.id + " " + control.title.get("en", "") + " " + control.title.get("es", "")
            )
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
