"""Loading and querying the cross-reference dataset.

The dataset is anchored on ISO/IEC 27002:2022 because it is the only one of the
catalogues that is a control set designed to be mapped from. Everything else is
derived: asking "what does ENS op.exp.8 correspond to?" is answered by finding
the ISO controls that point at it, which is why the index is built in both
directions at load time.

The list of frameworks is not hard-coded: it comes from ``frameworks.json``, so
adding a regime means adding a catalogue file, an entry there and a block per
row in ``mappings.json``.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DATA = pathlib.Path(__file__).parent / "data"
ANCHOR = "ISO"
#: Filled at load time from frameworks.json, in declaration order.
FRAMEWORKS = ("ISO", "ENS", "NIS2", "DORA", "PCI", "SOX")
TARGETS = ("ens", "nis2", "dora", "pci", "sox")

#: How completely an ISO control satisfies what the other framework asks for.
COVERAGE_ORDER = {"full": 0, "partial": 1, "none": 2}
COVERAGE_TEXT = {
    "full": {"en": "full", "es": "total"},
    "partial": {"en": "partial", "es": "parcial"},
    "none": {"en": "none", "es": "ninguna"},
}


@dataclass(frozen=True)
class Control:
    """One item of any of the catalogues."""

    framework: str
    id: str
    family: str
    family_title: Dict[str, str]
    title: Dict[str, str]
    layer: Optional[str] = None
    #: One-sentence description of what the control is about (ISO only so far).
    summary: Dict[str, str] = field(default_factory=dict)

    @property
    def ref(self) -> str:
        return f"{self.framework} {self.id}"

    def name(self, lang: str = "es") -> str:
        return self.title.get(lang, self.title.get("en", ""))

    def about(self, lang: str = "es") -> str:
        return self.summary.get(lang, self.summary.get("en", ""))

    def as_dict(self, lang: Optional[str] = None) -> Dict[str, Any]:
        if lang is None:
            out: Dict[str, Any] = {"framework": self.framework, "id": self.id, "family": self.family,
                                   "family_title": self.family_title, "title": self.title,
                                   "layer": self.layer}
            if self.summary:
                out["summary"] = self.summary
            return out
        out = {"framework": self.framework, "id": self.id,
               "family": self.family_title.get(lang, ""), "title": self.name(lang),
               "layer": self.layer}
        if self.summary:
            out["summary"] = self.about(lang)
        return out


@dataclass
class Link:
    """A correspondence from one ISO control to one item of another framework."""

    iso: str
    framework: str
    target: str
    coverage: str
    source: str
    status: str = "proposed"
    #: Why the correspondence is only partial: what the other regime asks for
    #: that the ISO control does not give. Present when coverage is "partial".
    rationale: Dict[str, str] = field(default_factory=dict)
    #: The rationale in three parts: what the ISO control already gives you
    #: ("covers"), what the other regime asks for beyond it ("adds") and what
    #: to build or evidence to close the gap ("close"). Each part bilingual.
    detail: Dict[str, Dict[str, str]] = field(default_factory=dict)

    @property
    def verified(self) -> bool:
        return self.status == "verified"

    def why(self, lang: str = "es") -> str:
        return self.rationale.get(lang, self.rationale.get("en", ""))

    def part(self, name: str, lang: str = "es") -> str:
        block = self.detail.get(name, {})
        return block.get(lang, block.get("en", ""))


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

    @property
    def framework_ids(self) -> List[str]:
        """Every framework, anchor first, in the order of frameworks.json."""
        return [f["id"] for f in self.frameworks]

    @property
    def target_ids(self) -> List[str]:
        """The frameworks the anchor is mapped to."""
        return [f for f in self.framework_ids if f != ANCHOR]

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
            if not self.control(ANCHOR, link.iso):
                missing.append(f"unknown ISO control {link.iso}")
        return sorted(set(missing))

    def unknown_sources(self) -> List[str]:
        return sorted({l.source for l in self.links if l.source not in self.sources})

    def partial_without_rationale(self) -> List[str]:
        """Partial correspondences that do not say why they are partial. Should be empty."""
        return sorted({f"{l.iso} -> {l.framework}" for l in self.links
                       if l.coverage == "partial" and not (l.rationale and l.detail)})

    def stats(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"iso_controls": len(self.controls.get(ANCHOR, {})),
                               "links": len(self.links),
                               "verified": sum(1 for l in self.links if l.verified),
                               "frameworks": self.target_ids}
        for framework in self.target_ids:
            counts = {"full": 0, "partial": 0, "none": 0}
            for iso_id in self.controls.get(ANCHOR, {}):
                counts[self.coverage.get(iso_id, {}).get(framework, "none")] += 1
            out[framework] = counts
        return out


def _load(name: str) -> Dict[str, Any]:
    with open(DATA / name, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load(data_dir: Optional[pathlib.Path] = None) -> Dataset:
    """Load the whole dataset and build both directions of the index."""
    global DATA, FRAMEWORKS, TARGETS
    if data_dir is not None:
        DATA = pathlib.Path(data_dir)

    frameworks = _load("frameworks.json")["frameworks"]
    FRAMEWORKS = tuple(f["id"] for f in frameworks)
    TARGETS = tuple(f["id"].lower() for f in frameworks if f["id"] != ANCHOR)

    controls: Dict[str, Dict[str, Control]] = {}
    for framework in FRAMEWORKS:
        raw = _load(f"controls_{framework.lower()}.json")
        controls[framework] = {
            item["id"]: Control(
                framework=framework, id=item["id"], family=item["family"],
                family_title=item["family_title"], title=item["title"],
                layer=item.get("layer"), summary=item.get("summary", {}),
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
        for key in TARGETS:
            framework = key.upper()
            block = row.get(key) or {}
            coverage[iso_id][framework] = block.get("coverage", "none")
            for target in block.get("ids", []):
                links.append(Link(iso=iso_id, framework=framework, target=target,
                                  coverage=block.get("coverage", "none"),
                                  source=block.get("source", ""),
                                  status=row.get("status", "proposed"),
                                  rationale=block.get("rationale", {}),
                                  detail=block.get("detail", {})))

    dataset = Dataset(controls=controls, links=links, sources=sources,
                      frameworks=frameworks, coverage=coverage)
    for link in links:
        dataset.forward.setdefault(link.iso, {}).setdefault(link.framework, []).append(link)
        dataset.reverse.setdefault(f"{link.framework}:{link.target}", []).append(link)
    return dataset
