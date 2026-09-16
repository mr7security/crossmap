"""Detailed rationale of every partial correspondence, one module per framework.

Each entry: (ISO id) -> dict(covers=(en, es), adds=(en, es), close=(en, es))
  covers - what implementing the ISO control already gives you towards the requirement
  adds   - what the other regime asks for beyond that, or where it is narrower
  close  - what to build or evidence to close the gap

Loaded by build_extend.py; the data lives in the JSON, these files are provenance.
"""
from . import ens, nis2, dora, pci, sox

DETAILS = {"ens": ens.D, "nis2": nis2.D, "dora": dora.D, "pci": pci.D, "sox": sox.D}
