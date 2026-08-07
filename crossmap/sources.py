"""Watching the source documents for changes.

A cross-reference is only as current as the documents it rests on, and those
documents move: ENISA revises its guidance, the CCN republishes a guide, Spain
finally transposes NIS2. This module records a fingerprint of each source and
tells you, later, which ones have moved and which rows of the dataset depend on
them — it does not attempt to re-derive the mapping, which is a judgement call
that belongs to a person.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .model import Dataset

STATE_FILE = "sources_state.json"
TIMEOUT = 20
USER_AGENT = "crossmap source watcher"


def _fingerprint(url: str) -> Dict[str, Any]:
    """Fetch enough of the document to tell whether it changed."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read(2_000_000)
            headers = response.headers
            return {
                "ok": True,
                "status": getattr(response, "status", 200),
                "etag": headers.get("ETag"),
                "last_modified": headers.get("Last-Modified"),
                "length": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def state_path(data_dir: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(data_dir) / STATE_FILE


def load_state(data_dir: pathlib.Path) -> Dict[str, Any]:
    path = state_path(data_dir)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def save_state(data_dir: pathlib.Path, state: Dict[str, Any]) -> None:
    with open(state_path(data_dir), "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=1, sort_keys=True)


def _changed(previous: Dict[str, Any], current: Dict[str, Any]) -> Optional[str]:
    """What moved, in the order of how much it is worth trusting."""
    if not previous or not previous.get("ok"):
        return None
    if not current.get("ok"):
        return None
    if previous.get("sha256") != current.get("sha256"):
        if previous.get("length") != current.get("length"):
            return f"content changed ({previous.get('length')} -> {current.get('length')} bytes)"
        return "content changed"
    if previous.get("etag") and previous.get("etag") != current.get("etag"):
        return "ETag changed"
    if previous.get("last_modified") != current.get("last_modified"):
        return f"Last-Modified changed ({current.get('last_modified')})"
    return None


def check(dataset: Dataset, data_dir: pathlib.Path, only: Optional[List[str]] = None,
          update: bool = True) -> Dict[str, Any]:
    """Re-fetch the watched sources and report what moved.

    ``update`` writes the new fingerprints, so the next run compares against
    today. Run it with ``update=False`` to see the difference without accepting
    it — useful when you want to review before the baseline shifts.
    """
    state = load_state(data_dir)
    report: Dict[str, Any] = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "first_run": not state, "results": [],
    }
    for source in dataset.sources.values():
        if only and source.id not in only:
            continue
        if not source.watch and not only:
            continue
        current = _fingerprint(source.url)
        previous = state.get(source.id, {})
        change = _changed(previous, current)
        affected = affected_rows(dataset, source.id)
        report["results"].append({
            "id": source.id, "url": source.url,
            "title": source.title, "ok": current.get("ok", False),
            "error": current.get("error"),
            "change": change,
            "first_seen": not previous,
            "previously_checked": previous.get("checked_at"),
            "affected_rows": len(affected),
            "affected_iso": affected[:20],
        })
        if update and current.get("ok"):
            state[source.id] = current
    if update:
        save_state(data_dir, state)
    report["changed"] = [r for r in report["results"] if r["change"]]
    report["unreachable"] = [r for r in report["results"] if not r["ok"]]
    return report


def affected_rows(dataset: Dataset, source_id: str) -> List[str]:
    """ISO controls whose correspondences cite this source."""
    return sorted({l.iso for l in dataset.links if l.source == source_id},
                  key=lambda i: (int(i.split(".")[0]), int(i.split(".")[1])))
