# crossmap

<sub>**mr7security** · seguridad ofensiva y defensiva · [github.com/mr7security](https://github.com/mr7security)</sub>

**Live demo → https://mr7security.github.io/crossmap/** — the interactive cross-reference in your browser (EN/ES).

**One control, six regimes.** Type `op.exp.8` and get the ISO 27002 controls it corresponds to, the NIS2 requirement it helps satisfy, the DORA article it maps onto, the PCI DSS requirement it contributes to and the SOX IT general control an auditor would test — or start from `req.8.4` of PCI DSS and walk it back to the ENS. The cross-reference works in every direction, in English and Spanish, from a command line or from a single self-contained HTML page you can email to a client. Every ISO control opens with a one-sentence description of what it is about, and every partial correspondence says **why** it is partial.

*Una consulta cruzada entre ISO/IEC 27001:2022, el ENS (RD 311/2022), NIS2, DORA, PCI DSS v4.0.1 y SOX (ITGC), tomando como eje los 93 controles de ISO/IEC 27002:2022. Funciona en cualquier direccion, en ingles y castellano, desde la linea de comandos o desde una pagina HTML autocontenida. Cada control ISO abre con una frase sobre de que trata, y cada correspondencia parcial explica por que lo es.*

---

## The thing worth understanding first

ISO 27001 and the ENS are **catalogues of controls**: 93 and 73 discrete items you can tick. NIS2 and DORA are not. NIS2 states ten obligations in Article 21(2) and details them, for some sectors only, in Implementing Regulation (EU) 2024/2690; DORA is a regulation with articles and technical standards addressed at financial entities. PCI DSS is a catalogue, but a **prescriptive** one: it fixes frequencies (quarterly scans, six-monthly access reviews), parameters (12-character passwords, 12-month log retention) and mechanisms (MFA into the CDE, file integrity monitoring) that ISO leaves to the organisation's judgement. And SOX has no IT controls at all: what auditors test under Section 404 is the classic set of **IT general controls** (access, changes, development, operations) that COSO and PCAOB AS 2201 treat as the technology floor of internal control over financial reporting.

A six-column table of "equivalent controls" would therefore be a fiction. What this dataset records instead is **how far an ISO control takes you** towards each obligation:

| | meaning |
|---|---|
| **full** | implementing the ISO control substantially satisfies the requirement |
| **partial** | it contributes, but the other regime asks for more, or for something narrower |
| **none** | no correspondence |

Every **partial** row carries a rationale, in both languages, in three parts: **what the ISO control already gives you**, **what the other regime asks for beyond it** — the six-monthly review PCI DSS 7.2.4 fixes, the SOC 1 report SOX expects from a service organisation, the 24-hour early warning of NIS2 Article 23 — and **what to build or evidence to close the gap**. That is the text an auditor or a consultant actually needs when the question is "we are ISO certified, what is left?". The `Parciales` sheet of the spreadsheet lists all 219 of them, one per row, ready to filter.

And it records the opposite too: **what each regime asks for that ISO 27001 does not give you at all**. Today that is ten DORA articles — supervisory reporting, threat-led penetration testing, the harmonisation mandates — one PCI DSS requirement (12.3, the targeted risk analyses, which live in ISO 27001 clause 6 rather than in a 27002 control), three SOX items (real-time disclosure, the CEO/CFO criminal certification and data conversion controls) and nothing at all in the ENS or in NIS2, which is itself a finding worth being able to state.

## Install and use

```bash
git clone https://github.com/mr7security/crossmap.git
cd crossmap
pip install -e .            # optional; python -m crossmap works without installing
```

Python 3.9+, no dependencies. `openpyxl` only for the spreadsheet.

```bash
# A control and everything it corresponds to, from any framework
python -m crossmap show 8.15              # ISO: prints what the control is about, then each regime
python -m crossmap show op.exp.8          # ENS
python -m crossmap show art.12 --lang en  # DORA
python -m crossmap show cir.3.2           # NIS2
python -m crossmap show req.8.4           # PCI DSS ("PCI 8.4" also works; a bare "8.4" is always ISO)
python -m crossmap show acc.1             # SOX / ITGC ("SOX 404" reaches sec.404)

# Free text, accent and case insensitive, across titles and the ISO summaries
python -m crossmap search criptografia
python -m crossmap search "copias de seguridad"
python -m crossmap search MFA

# What ISO 27001 does not cover
python -m crossmap gaps
python -m crossmap gaps SOX

# Deliverables
python -m crossmap html -o equivalencias.html     # interactive, self-contained, bilingual
python -m crossmap xlsx -o equivalencias.xlsx     # one row per ISO control + gaps + every partial with its rationale
python -m crossmap export -o dataset.json         # the whole thing, for your own tooling

# Housekeeping
python -m crossmap stats
python -m crossmap verify
```

## Keeping it honest over time

The documents underneath this move: ENISA revises its guidance, the CCN republishes a guide, and Spain still has to transpose NIS2. So the dataset carries a fingerprint of every source and can tell you what has shifted:

```bash
python -m crossmap check-sources             # re-fetch, compare, update the baseline
python -m crossmap check-sources --dry-run    # look without accepting the change
python -m crossmap check-sources --only CCN-STIC-825
```

It reports which documents changed and **which rows depend on them**, then stops. It does not try to re-derive the mapping, because that is a judgement call that belongs to a person. Exit code `2` when something moved, so it can run unattended:

```bash
0 7 * * 1  cd /ruta/crossmap && python -m crossmap check-sources || mail -s "crossmap: fuentes cambiadas" tu@correo
```

## Sources, and the status of every row

| Source | Used for |
|---|---|
| ISO/IEC 27002:2022 | The 93 control titles (titles only; the standard is copyrighted and is not reproduced) |
| RD 311/2022, Annex II | The 73 ENS measures, taken from the text published by the CCN |
| CCN-STIC 825, independent annex | The reference correspondence between ISO 27001:2022 and the ENS |
| Directive (EU) 2022/2555, Art. 21(2) | The ten NIS2 obligations |
| Implementing Regulation (EU) 2024/2690 | The 49 detailed NIS2 requirements |
| ENISA Technical Implementation Guidance v1.0 + mapping table v1.2 | The NIS2 side of the correspondences |
| Regulation (EU) 2022/2554 and its RTS | DORA articles and technical standards |
| PCI DSS v4.0.1 (PCI SSC, June 2024) | The 63 second-level requirements (x.y) of the twelve principal requirements |
| Sarbanes-Oxley Act of 2002 | Sections 302, 404, 409, 802 and 906 |
| COSO 2013 and PCAOB AS 2201 | The IT general controls tested under Section 404 (a synthesis of audit practice, not an official taxonomy) |

**Every row is marked `proposed` until a human confirms it against the cited document.** That is deliberate: the correspondences here are a reading of the sources, made carefully, but a mapping is an editorial act and an unverified claim presented as fact is exactly what gets an auditor's attention for the wrong reason. `crossmap stats` reports how many rows are verified; flip a row to `verified` in `crossmap/data/mappings.json` as you check it.

The one-sentence descriptions of the ISO controls are the author's own paraphrases of each control's purpose, written for orientation; the text of ISO/IEC 27002 is copyrighted and is not reproduced. The PCI DSS side uses the requirement titles at the x.y level only; the detailed requirements and testing procedures are in the standard, which is free to download.

Three caveats worth stating plainly. The SOX catalogue is not official: SOX itself contains no IT controls, so the ITGC list here is the four-domain structure auditors actually test, and another audit firm would slice it slightly differently. Implementing Regulation 2024/2690 is legally binding only for digital infrastructure, ICT service management and digital provider entities; for every other sector it is used here as the best available articulation of Article 21(2), not as binding law. And the Spanish law transposing NIS2 was not in force when this dataset was written, so the NIS2 side will need revisiting when it is — which is precisely what the source watcher is for.

## Project structure

```
crossmap/
├── crossmap/
│   ├── data/            # the dataset: six catalogues, the mapping (with rationales), the sources
│   ├── model.py         # loading and the two-way index
│   ├── query.py         # resolution, equivalence in any direction, search, gaps
│   ├── sources.py       # fingerprinting and change detection
│   ├── report_html.py   # the self-contained interactive page
│   ├── report_xlsx.py   # the spreadsheet
│   └── cli.py
├── build_*.py           # the scripts that generated the JSON catalogues, kept as provenance
│                        # (build_extend.py holds the PCI/SOX mapping and every short rationale)
├── details/             # the three-part rationale of every partial row, one module per framework
└── tests/
```

```bash
python -m unittest discover -s tests
```

## Legal notice / Aviso legal

This is a working aid, not legal advice, and not a compliance certification. The correspondences express how the author reads the cited documents; the applicability of any regime to a given organisation, and the sufficiency of any measure, is decided by that organisation and its auditors.

*Esta es una herramienta de trabajo, no asesoramiento juridico ni una certificacion de cumplimiento. Las correspondencias expresan como el autor lee los documentos citados; la aplicabilidad de cada regimen a una organizacion concreta, y la suficiencia de cualquier medida, la deciden esa organizacion y sus auditores.*

## License

MIT — see [LICENSE](LICENSE).

---

<sub>Part of the **mr7security** toolset, alongside [netscan](https://github.com/mr7security/netscan) ·
[webscan](https://github.com/mr7security/webscan) · [logscan](https://github.com/mr7security/logscan) ·
[spoofscan](https://github.com/mr7security/spoofscan).</sub>
