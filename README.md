# crossmap

<sub>**mr7security** · seguridad ofensiva y defensiva · [github.com/mr7security](https://github.com/mr7security)</sub>

**One control, four regimes.** Type `op.exp.8` and get the ISO 27002 controls it corresponds to, the NIS2 requirement it helps satisfy and the DORA article it maps onto — or start from `art.12` of DORA and walk it back to the ENS. The cross-reference works in every direction, in English and Spanish, from a command line or from a single self-contained HTML page you can email to a client.

*Una consulta cruzada entre ISO/IEC 27001:2022, el ENS (RD 311/2022), NIS2 y DORA, tomando como eje los 93 controles de ISO/IEC 27002:2022. Funciona en cualquier direccion, en ingles y castellano, desde la linea de comandos o desde una pagina HTML autocontenida.*

---

## The thing worth understanding first

ISO 27001 and the ENS are **catalogues of controls**: 93 and 73 discrete items you can tick. NIS2 and DORA are not. NIS2 states ten obligations in Article 21(2) and details them, for some sectors only, in Implementing Regulation (EU) 2024/2690; DORA is a regulation with articles and technical standards addressed at financial entities.

A four-column table of "equivalent controls" would therefore be a fiction. What this dataset records instead is **how far an ISO control takes you** towards each obligation:

| | meaning |
|---|---|
| **full** | implementing the ISO control substantially satisfies the requirement |
| **partial** | it contributes, but the other regime asks for more, or for something narrower |
| **none** | no correspondence |

And it records the opposite too, which is the half people actually need: **what each regime asks for that ISO 27001 does not give you**. Today that is ten DORA articles — supervisory reporting, threat-led penetration testing, the harmonisation mandates — and nothing at all in the ENS or in NIS2, which is itself a finding worth being able to state.

## Install and use

```bash
git clone https://github.com/mr7security/crossmap.git
cd crossmap
pip install -e .            # optional; python -m crossmap works without installing
```

Python 3.9+, no dependencies. `openpyxl` only for the spreadsheet.

```bash
# A control and everything it corresponds to, from any framework
python -m crossmap show 8.15
python -m crossmap show op.exp.8
python -m crossmap show art.12 --lang en
python -m crossmap show cir.3.2

# Free text, accent and case insensitive
python -m crossmap search criptografia
python -m crossmap search "copias de seguridad"

# What ISO 27001 does not cover
python -m crossmap gaps
python -m crossmap gaps DORA

# Deliverables
python -m crossmap html -o equivalencias.html     # interactive, self-contained, bilingual
python -m crossmap xlsx -o equivalencias.xlsx     # one row per ISO control + a gaps sheet
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

**Every row is marked `proposed` until a human confirms it against the cited document.** That is deliberate: the correspondences here are a reading of the sources, made carefully, but a mapping is an editorial act and an unverified claim presented as fact is exactly what gets an auditor's attention for the wrong reason. `crossmap stats` reports how many rows are verified; flip a row to `verified` in `crossmap/data/mappings.json` as you check it.

Two caveats worth stating plainly. Implementing Regulation 2024/2690 is legally binding only for digital infrastructure, ICT service management and digital provider entities; for every other sector it is used here as the best available articulation of Article 21(2), not as binding law. And the Spanish law transposing NIS2 was not in force when this dataset was written, so the NIS2 side will need revisiting when it is — which is precisely what the source watcher is for.

## Project structure

```
crossmap/
├── crossmap/
│   ├── data/            # the dataset: four catalogues, the mapping, the sources
│   ├── model.py         # loading and the two-way index
│   ├── query.py         # resolution, equivalence in any direction, search, gaps
│   ├── sources.py       # fingerprinting and change detection
│   ├── report_html.py   # the self-contained interactive page
│   ├── report_xlsx.py   # the spreadsheet
│   └── cli.py
├── build_*.py           # the scripts that generated the JSON catalogues, kept as provenance
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
