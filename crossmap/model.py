"""Loading and querying the cross-reference dataset.

The dataset is anchored on ISO/IEC 27002:2022 because it is the only one of the
four that is a control catalogue designed to be mapped from. Everything else is
derived: asking "what does ENS op.exp.8 correspond to?" is answered by finding
the ISO controls that point at it, which is why the index is built in both
directions at load time.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DATA = pathlib.Path(__file__).parent / "data"
FRAMEWORKS = ("ISO", "ENS", "NIS2", "DORA")
TARGETS = ("ens", "nis2", "dora")

#: How completely an ISO control satisfies what the other framework asks for.
COVERAGE_ORDER = {"full": 0, "partial": 1, "none": 2}
COVERAGE_TEXT = {
    "full": {"en": "full", "es": "total"},
    "partial": {"en": "partial", "es": "parcial"},
    "none": {"en": "none", "es": "ninguna"},
}


@dataclass(frozen=True)
class Control:
    """One item of any of the four catalogues."""

    framework: str
    id: str
    family: str
    family_title: Dict[str, str]
    title: Dict[str, str]
    layer: Optional[str] = None

    @property
    def ref(self) -> str:
        return f"{self.framework} {self.id}"

    def name(self, lang: str = "es") -> str:
        return self.title.get(lang, self.title.get("en", ""))

    def as_dict(self, lang: Optional[str] = None) -> Dict[str, Any]:
        if lang is None:
            return {"framework": self.framework, "id": self.id, "family": self.family,
                    "family_title": self.family_title, "title": self.title, "layer": self.layer}
        return {"framework": self.framework, "id": self.id,
                "family": self.family_title.get(lang, ""), "title": self.name(lang),
                "layer": self.layer}


@dataclass
class Link:
    """A correspondence from one ISO control to one item of another framework."""

    iso: str
    framework: str
    target: str
    coverage: str
    source: str
    status: str = "proposed"

    @property
    def verified(self) -> bool:
        return self.status == "verified"


@dataclass
class Source:
    id: str
    kind: str
    title: Dict[str, str]
    url: str
    watch: bool = True
    note: Dict[str, str] = field(default_factory=dict)


@dataclass
class Dataset:
    controls: Dict[str, Dict[str, Control]]      # framework -> id -> Control
    links: List[Link]
    sources: Dict[str, Source]
    frameworks: List[Dict[str, Any]]
    #: ISO id -> framework -> [Link]
    forward: Dict[str, Dict[str, List[Link]]] = field(default_factory=dict)
    #: "FRAMEWORK:id" -> [Link]
    reverse: Dict[str, List[Link]] = field(default_factory=dict)
    coverage: Dict[str, Dict[str, str]] = field(default_factory=dict)   # iso -> fw -> coverage

    def control(self, framework: str, control_id: str) -> Optional[Control]:
        return self.controls.get(framework, {}).get(control_id)

    def all_controls(self, framework: str) -> List[Control]:
        return list(self.controls.get(framework, {}).values())

    def unknown_references(self) -> List[str]:
        """Links pointing at an id that no catalogue defines. Should be empty."""
        missing = []
        for link in self.links:
            if not self.control(link.framework, link.target):
                missing.append(f"{link.iso} -> {link.framework} {link.target}")
            if not self.control("ISO", link.iso):
                missing.append(f"unknown ISO control {link.iso}")
        return sorted(set(missing))

    def unknown_sources(self) -> List[str]:
        return sorted({l.source for l in self.links if l.source not in self.sources})

    def stats(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"iso_controls": len(self.controls.get("ISO", {})),
                               "links": len(self.links),
                               "verified": sum(1 for l in self.links if l.verified)}
        for framework in ("ENS", "NIS2", "DORA"):
            counts = {"full": 0, "partial": 0, "none": 0}
            for iso_id in self.controls.get("ISO", {}):
                counts[self.coverage.get(iso_id, {}).get(framework, "none")] += 1
            out[framework] = counts
        return out


def _load(name: str) -> Dict[str, Any]:
    with open(DATA / name, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load(data_dir: Optional[pathlib.Path] = None) -> Dataset:
    """Load the whole dataset and build both directions of the index."""
    global DATA
    if data_dir is not None:
        DATA = pathlib.Path(data_dir)

    controls: Dict[str, Dict[str, Control]] = {}
    for framework, filename in (("ISO", "controls_iso.json"), ("ENS", "controls_ens.json"),
                                ("NIS2", "controls_nis2.json"), ("DORA", "controls_dora.json")):
        raw = _load(filename)
        controls[framework] = {
            item["id"]: Control(
                framework=framework, id=item["id"], family=item["family"],
                family_title=item["family_title"], title=item["title"],
                layer=item.get("layer"),
            )
            for item in raw["items"]
        }

    sources = {s["id"]: Source(id=s["id"], kind=s["kind"], title=s["title"], url=s["url"],
                               watch=s.get("watch", True), note=s.get("note", {}))
               for s in _load("sources.json")["sources"]}

    links: List[Link] = []
    coverage: Dict[str, Dict[str, str]] = {}
    for row in _load("mappings.json")["rows"]:
        iso_id = row["iso"]
        coverage[iso_id] = {}
        for key, framework in (("ens", "ENS"), ("nis2", "NIS2"), ("dora", "DORA")):
            block = row.get(key) or {}
            coverage[iso_id][framework] = block.get("coverage", "none")
            for target in block.get("ids", []):
                links.append(Link(iso=iso_id, framework=framework, target=target,
                                  coverage=block.get("coverage", "none"),
                                  source=block.get("source", ""),
                                  status=row.get("status", "proposed")))

    dataset = Dataset(controls=controls, links=links, sources=sources,
                      frameworks=_load("frameworks.json")["frameworks"], coverage=coverage)
    for link in links:
        dataset.forward.setdefault(link.iso, {}).setdefault(link.framework, []).append(link)
        dataset.reverse.setdefault(f"{link.framework}:{link.target}", []).append(link)
    return dataset
