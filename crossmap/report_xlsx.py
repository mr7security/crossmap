"""The cross-reference as a spreadsheet, one row per ISO control.

Three sheets: the cross-reference itself (ids, coverage and, when partial, the
reason, per framework), the gaps, and a flat list of every partial
correspondence with its rationale, which is the sheet an auditor filters.
"""
from __future__ import annotations

from typing import Any, List

from .model import ANCHOR, COVERAGE_TEXT, Dataset

FILL = {"full": "C6EFCE", "partial": "FFEB9C", "none": "F2F2F2"}


def write(path: str, dataset: Dataset, lang: str = "es") -> str:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("openpyxl is required for the spreadsheet: pip install openpyxl") from exc

    es = lang == "es"
    targets = dataset.target_ids
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Equivalencias" if es else "Cross-reference"

    headers = (["Control ISO", "Titulo ISO", "De que trata", "Tema"] if es else
               ["ISO control", "ISO title", "What it is about", "Theme"])
    widths = [12, 40, 60, 22]
    wrap_columns = {2, 3, 4}
    coverage_columns = {}
    for framework in targets:
        headers += ([framework, f"Cobertura {framework}", f"Por que parcial ({framework})"] if es else
                    [framework, f"{framework} coverage", f"Why partial ({framework})"])
        column = len(headers)
        coverage_columns[column - 1] = framework
        wrap_columns.update({column - 2, column})
        widths += [24, 13, 55]
    headers += ["Fuentes", "Estado"] if es else ["Sources", "Status"]
    widths += [28, 12]

    for column, header in enumerate(headers, start=1):
        cell = sheet.cell(row=1, column=column, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F3864")
        cell.alignment = Alignment(vertical="center", wrap_text=True)

    row_index = 2
    for control in dataset.all_controls(ANCHOR):
        links = dataset.forward.get(control.id, {})
        values: List[Any] = [control.id, control.name(lang), control.about(lang),
                             control.family_title.get(lang, "")]
        sources = set()
        for framework in targets:
            group = links.get(framework, [])
            values.append(", ".join(t.target for t in group) or "—")
            coverage = dataset.coverage.get(control.id, {}).get(framework, "none")
            values.append(COVERAGE_TEXT[coverage][lang])
            values.append(next((t.why(lang) for t in group if t.rationale), ""))
            sources.update(t.source for t in group)
        values.append(", ".join(sorted(sources)) or "—")
        values.append(next(iter({l.status for group in links.values() for l in group}), "proposed"))
        for column, value in enumerate(values, start=1):
            cell = sheet.cell(row=row_index, column=column, value=value)
            cell.alignment = Alignment(vertical="top", wrap_text=column in wrap_columns)
        for column, framework in coverage_columns.items():
            coverage = dataset.coverage.get(control.id, {}).get(framework, "none")
            sheet.cell(row=row_index, column=column).fill = PatternFill("solid", fgColor=FILL[coverage])
        row_index += 1

    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = "C2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{row_index - 1}"
    mark = sheet.cell(row=row_index + 1, column=1,
                      value="crossmap · mr7security · github.com/mr7security/crossmap")
    mark.font = Font(size=9, color="808080")

    # Second sheet: what each regime asks for that ISO does not cover.
    from .query import orphans
    gaps = workbook.create_sheet("Huecos" if es else "Gaps")
    gap_headers = (["Marco", "Referencia", "Titulo", "Familia"] if es else
                   ["Framework", "Reference", "Title", "Family"])
    for column, header in enumerate(gap_headers, start=1):
        cell = gaps.cell(row=1, column=column, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="7B2D26")
    index = 2
    for framework in targets:
        for control in orphans(dataset, framework):
            for column, value in enumerate(
                [framework, control.id, control.name(lang), control.family_title.get(lang, "")],
                start=1,
            ):
                gaps.cell(row=index, column=column, value=value).alignment = Alignment(
                    vertical="top", wrap_text=column in (3, 4))
            index += 1
    for column, width in enumerate([12, 18, 60, 40], start=1):
        gaps.column_dimensions[get_column_letter(column)].width = width
    gaps.freeze_panes = "A2"

    # Third sheet: every partial correspondence and why it is partial.
    partial = workbook.create_sheet("Parciales" if es else "Partial")
    partial_headers = (["Control ISO", "Titulo ISO", "Marco", "Referencias", "Por que es parcial",
                        "Lo que ISO te da", "Lo que pide el regimen", "Para cerrar el hueco", "Fuente"] if es
                       else ["ISO control", "ISO title", "Framework", "References", "Why it is partial",
                             "What ISO gives you", "What the regime asks for", "To close the gap", "Source"])
    for column, header in enumerate(partial_headers, start=1):
        cell = partial.cell(row=1, column=column, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="8A6914")
    index = 2
    for control in dataset.all_controls(ANCHOR):
        for framework in targets:
            group = dataset.forward.get(control.id, {}).get(framework, [])
            if not group or group[0].coverage != "partial":
                continue
            values = [control.id, control.name(lang), framework,
                      ", ".join(t.target for t in group), group[0].why(lang),
                      group[0].part("covers", lang), group[0].part("adds", lang),
                      group[0].part("close", lang), group[0].source]
            for column, value in enumerate(values, start=1):
                partial.cell(row=index, column=column, value=value).alignment = Alignment(
                    vertical="top", wrap_text=column in (2, 4, 5, 6, 7, 8))
            index += 1
    for column, width in enumerate([12, 36, 10, 24, 60, 50, 70, 55, 20], start=1):
        partial.column_dimensions[get_column_letter(column)].width = width
    partial.freeze_panes = "A2"
    partial.auto_filter.ref = f"A1:I{index - 1}"

    workbook.save(path)
    return path
