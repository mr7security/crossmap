"""Command line interface."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import List, Optional

from . import __version__
from .model import COVERAGE_TEXT, load
from .query import equivalents, orphans, resolve, search

BAR = "-" * 74


def build_parser() -> argparse.ArgumentParser:
    # The global options live in a parent parser so that they work both before
    # and after the subcommand: "crossmap --lang en show 8.15" and
    # "crossmap show 8.15 --lang en" are the same thing to anyone typing them.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--lang", choices=["en", "es"], default="es")
    common.add_argument("--data", metavar="DIR", help="use an alternative data directory")

    parser = argparse.ArgumentParser(
        prog="crossmap", parents=[common],
        description=("Cross-reference between ISO/IEC 27001:2022, the Spanish ENS (RD 311/2022), "
                     "NIS2 and DORA, anchored on the 93 controls of ISO/IEC 27002:2022."),
    )
    sub = parser.add_subparsers(dest="command", parser_class=lambda **kw: argparse.ArgumentParser(
        parents=[common], **kw))

    show = sub.add_parser("show", help="show a control and its equivalents in the other frameworks")
    show.add_argument("reference", help="e.g. 8.15, ISO 8.15, op.exp.8, cir.3.2, art.12")

    find = sub.add_parser("search", help="free text search across the four catalogues")
    find.add_argument("text", nargs="+")

    gaps = sub.add_parser("gaps", help="requirements with no ISO 27002 equivalent")
    gaps.add_argument("framework", nargs="?", choices=["ENS", "NIS2", "DORA"],
                      help="restrict to one framework")

    html = sub.add_parser("html", help="write the interactive HTML cross-reference")
    html.add_argument("-o", "--output", default="crossmap.html")

    xlsx = sub.add_parser("xlsx", help="write the spreadsheet (needs openpyxl)")
    xlsx.add_argument("-o", "--output", default="crossmap.xlsx")

    export = sub.add_parser("export", help="dump the whole dataset as JSON")
    export.add_argument("-o", "--output", default="-")

    check = sub.add_parser("check-sources", help="re-fetch the sources and report what changed")
    check.add_argument("--only", action="append", metavar="ID", help="check a single source")
    check.add_argument("--dry-run", action="store_true",
                       help="report differences without moving the baseline")
    check.add_argument("--json", action="store_true", help="machine readable output")

    sub.add_parser("stats", help="dataset coverage summary")
    sub.add_parser("verify", help="integrity checks over the dataset itself")

    parser.add_argument("--version", action="version",
                        version=f"crossmap {__version__} · mr7security · "
                                "https://github.com/mr7security/crossmap")
    return parser


def _print_control(control, lang: str, indent: str = "") -> None:
    print(f"{indent}{control.ref:<16} {control.name(lang)}")
    print(f"{indent}{'':<16} {control.family_title.get(lang, '')}")


def cmd_show(dataset, reference: str, lang: str) -> int:
    control = resolve(dataset, reference)
    if not control:
        print(f"error: '{reference}' does not match any control", file=sys.stderr)
        candidates = search(dataset, reference, lang)[:5]
        if candidates:
            print("did you mean:", ", ".join(c.ref for c in candidates), file=sys.stderr)
        return 1

    print(BAR)
    _print_control(control, lang)
    print(BAR)
    found = equivalents(dataset, control)
    labels = {"en": "no correspondence recorded", "es": "sin correspondencia registrada"}
    for framework in ("ISO", "ENS", "NIS2", "DORA"):
        if framework == control.framework:
            continue
        items = found.get(framework, [])
        print(f"\n{framework}")
        if not items:
            print(f"  ({labels[lang]})")
            continue
        for entry in items:
            target = entry["control"]
            coverage = COVERAGE_TEXT.get(entry["coverage"], {}).get(lang, entry["coverage"])
            print(f"  {target.id:<14} [{coverage:<7}] {target.name(lang)}")
            if entry.get("source"):
                print(f"  {'':<14}  ← {entry['source']}")
    return 0


def cmd_search(dataset, text: str, lang: str) -> int:
    results = search(dataset, text, lang)
    if not results:
        print("nothing found" if lang == "en" else "sin resultados")
        return 1
    for control in results:
        print(f"{control.ref:<16} {control.name(lang)}")
    print(f"\n{len(results)} " + ("results" if lang == "en" else "resultados"))
    return 0


def cmd_gaps(dataset, framework: Optional[str], lang: str) -> int:
    header = {"en": "Requirements with no ISO 27002 equivalent",
              "es": "Requisitos sin equivalente en ISO 27002"}
    print(header[lang])
    print(BAR)
    total = 0
    for name in ([framework] if framework else ["ENS", "NIS2", "DORA"]):
        missing = orphans(dataset, name)
        total += len(missing)
        print(f"\n{name} ({len(missing)})")
        for control in missing:
            print(f"  {control.id:<14} {control.name(lang)}")
    print(f"\n{total} " + ("in total" if lang == "en" else "en total"))
    return 0


def cmd_check(dataset, args, data_dir: pathlib.Path, lang: str) -> int:
    from .sources import check
    report = check(dataset, data_dir, only=args.only, update=not args.dry_run)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if report["first_run"]:
        print("first run: recording the current state of every source as the baseline"
              if lang == "en" else
              "primera ejecucion: se registra el estado actual de cada fuente como referencia")
    for result in report["results"]:
        mark = "!" if result["change"] else ("x" if not result["ok"] else ".")
        print(f"[{mark}] {result['id']:<22} {result['title'].get(lang, '')[:60]}")
        if result["change"]:
            print(f"      {result['change']}")
            print("      " + ("affects" if lang == "en" else "afecta a") +
                  f" {result['affected_rows']} " +
                  ("ISO controls: " if lang == "en" else "controles ISO: ") +
                  ", ".join(result["affected_iso"][:12]))
        elif not result["ok"]:
            print(f"      {result['error']}")
    changed = len(report["changed"])
    print(f"\n{changed} " + ("source(s) changed" if lang == "en" else "fuente(s) con cambios"))
    if changed:
        print("review the affected rows and set their status to verified once checked"
              if lang == "en" else
              "revise las filas afectadas y marque su estado como verificado cuando las compruebe")
    return 2 if changed else 0


def cmd_verify(dataset, lang: str) -> int:
    problems: List[str] = []
    problems += [f"broken reference: {r}" for r in dataset.unknown_references()]
    problems += [f"unknown source: {s}" for s in dataset.unknown_sources()]
    for framework in ("ENS", "NIS2", "DORA"):
        missing = orphans(dataset, framework)
        if len(missing) > len(dataset.all_controls(framework)) / 2:
            problems.append(f"{framework}: more than half of the catalogue is unmapped")
    if problems:
        for problem in problems:
            print(f"[!] {problem}")
        return 1
    print("dataset is internally consistent" if lang == "en"
          else "el conjunto de datos es internamente consistente")
    stats = dataset.stats()
    print(f"    {stats['links']} " + ("correspondences, " if lang == "en" else "correspondencias, ")
          + f"{stats['verified']} " + ("verified" if lang == "en" else "verificadas"))
    return 0


def cmd_stats(dataset, lang: str) -> int:
    stats = dataset.stats()
    print(f"ISO 27002: {stats['iso_controls']} " + ("controls" if lang == "en" else "controles"))
    print(f"{stats['links']} " + ("correspondences" if lang == "en" else "correspondencias")
          + f" | {stats['verified']} " + ("verified" if lang == "en" else "verificadas"))
    print(BAR)
    for framework in ("ENS", "NIS2", "DORA"):
        counts = stats[framework]
        total = sum(counts.values())
        print(f"{framework:<6} " + " ".join(
            f"{COVERAGE_TEXT[k][lang]}: {counts[k]:>3} ({counts[k]*100//total:>2}%)"
            for k in ("full", "partial", "none")))
    print(BAR)
    for framework in ("ENS", "NIS2", "DORA"):
        print(f"{framework:<6} " + ("without ISO equivalent: " if lang == "en"
                                    else "sin equivalente ISO: ") + str(len(orphans(dataset, framework))))
    print(BAR)
    print("crossmap · mr7security · https://github.com/mr7security")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.command:
        build_parser().print_help()
        return 1

    data_dir = pathlib.Path(args.data) if args.data else None
    try:
        dataset = load(data_dir)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: cannot load the dataset: {exc}", file=sys.stderr)
        return 1
    from .model import DATA
    lang = args.lang

    if args.command == "show":
        return cmd_show(dataset, args.reference, lang)
    if args.command == "search":
        return cmd_search(dataset, " ".join(args.text), lang)
    if args.command == "gaps":
        return cmd_gaps(dataset, args.framework, lang)
    if args.command == "stats":
        return cmd_stats(dataset, lang)
    if args.command == "verify":
        return cmd_verify(dataset, lang)
    if args.command == "check-sources":
        return cmd_check(dataset, args, DATA, lang)
    if args.command == "html":
        from .report_html import render
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(render(dataset))
        except OSError as exc:
            print(f"error: cannot write the page: {exc}", file=sys.stderr)
            return 1
        print(f"[+] HTML -> {args.output}")
        return 0
    if args.command == "xlsx":
        from .report_xlsx import write
        try:
            write(args.output, dataset, lang)
        except (RuntimeError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"[+] XLSX -> {args.output}")
        return 0
    if args.command == "export":
        payload = {
            "version": __version__,
            "frameworks": dataset.frameworks,
            "controls": {fw: [c.as_dict() for c in dataset.all_controls(fw)]
                         for fw in ("ISO", "ENS", "NIS2", "DORA")},
            "links": [vars(l) for l in dataset.links],
            "sources": [vars(s) for s in dataset.sources.values()],
            "stats": dataset.stats(),
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output == "-":
            print(text)
            return 0
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            print(f"error: cannot write the export: {exc}", file=sys.stderr)
            return 1
        print(f"[+] JSON -> {args.output}")
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
