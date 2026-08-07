"""The whole cross-reference as one self-contained, searchable HTML page.

The dataset is embedded as JSON and the page does the querying in the browser,
so the file works offline, from a USB stick, or attached to an email — which is
how a reference like this actually gets used.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from .model import Dataset
from .query import orphans

CSS = """
:root{--bg:#0f1218;--panel:#161b24;--panel2:#1c2230;--line:#273042;--fg:#e6ebf2;
--muted:#93a0b4;--accent:#4da3ff;--full:#2eb872;--partial:#d9a21e;--none:#6b7280;
--iso:#4da3ff;--ens:#e0654a;--nis2:#9b6dd6;--dora:#22a3a3}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 22px 70px}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;
border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:22px;flex-wrap:wrap}
h1{font-size:25px;margin:0 0 4px;letter-spacing:-.4px}
.sub{color:var(--muted);font-size:14px;margin:0;max-width:70ch}
.toggle{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:5px;display:flex;gap:4px}
.toggle button{background:none;border:0;color:var(--muted);padding:6px 13px;border-radius:6px;
cursor:pointer;font:inherit;font-size:13px}
.toggle button.on{background:var(--accent);color:#04101f;font-weight:600}
.search{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.search input{flex:1;min-width:260px;background:var(--panel);border:1px solid var(--line);
border-radius:9px;color:var(--fg);padding:11px 14px;font:inherit}
.search input:focus{outline:none;border-color:var(--accent)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:999px;
padding:5px 13px;font-size:13px;cursor:pointer}
.chip.on{border-color:var(--accent);color:var(--accent)}
.count{color:var(--muted);font-size:13px;margin:0 0 12px}
.row{background:var(--panel);border:1px solid var(--line);border-radius:11px;margin-bottom:10px;
overflow:hidden}
.row>summary{cursor:pointer;padding:13px 16px;display:flex;gap:12px;align-items:baseline;
flex-wrap:wrap;list-style:none}
.row>summary::-webkit-details-marker{display:none}
.row>summary:hover{background:var(--panel2)}
.id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;font-weight:700;
padding:3px 8px;border-radius:6px;color:#06090f;white-space:nowrap}
.id.ISO{background:var(--iso)}.id.ENS{background:var(--ens)}
.id.NIS2{background:var(--nis2)}.id.DORA{background:var(--dora)}
.rt{flex:1;min-width:200px}
.cov{font-size:11px;font-weight:700;letter-spacing:.05em;padding:2px 7px;border-radius:5px;
text-transform:uppercase}
.cov.full{background:rgba(46,184,114,.18);color:var(--full)}
.cov.partial{background:rgba(217,162,30,.18);color:var(--partial)}
.cov.none{background:rgba(107,114,128,.18);color:var(--none)}
.body{padding:4px 16px 16px;border-top:1px solid var(--line)}
.fw{margin-top:14px}
.fw h4{margin:0 0 7px;font-size:12px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
.item{display:flex;gap:10px;align-items:baseline;padding:6px 0;border-bottom:1px solid rgba(39,48,66,.6)}
.item:last-child{border-bottom:0}
.item .t{flex:1}
.item small{color:var(--muted);font-size:12px}
.empty{color:var(--muted);font-size:13.5px;font-style:italic}
.src{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;color:var(--muted);
border:1px solid var(--line);border-radius:5px;padding:1px 6px}
.brand{display:inline-flex;align-items:center;gap:7px;font-family:ui-monospace,SFMono-Regular,
Menlo,monospace;font-size:12px;letter-spacing:.06em;color:var(--muted);border:1px solid var(--line);
border-radius:999px;padding:4px 11px;text-decoration:none;margin-top:10px}
.brand:hover{color:var(--accent);border-color:var(--accent)}
.brand b{color:var(--fg);font-weight:600;letter-spacing:.02em}
footer .brand{margin-top:12px}
.legend{background:var(--panel2);border:1px solid var(--line);border-radius:11px;padding:16px 18px;
margin-bottom:20px;font-size:14px;color:#cfd8e5}
.legend b{color:var(--fg)}
.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-bottom:20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:15px 16px}
.card h3{margin:0 0 3px;font-size:15px}
.card p{margin:0;color:var(--muted);font-size:13px}
.bar{display:flex;height:7px;border-radius:4px;overflow:hidden;margin-top:11px;background:var(--line)}
.bar i{display:block;height:100%}
h2{font-size:18px;margin:34px 0 12px}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px}
.es{display:none}
body.lang-es .en{display:none}body.lang-es .es{display:inline}
body.lang-es p.es,body.lang-es div.es,body.lang-es span.es{display:inline}
body.lang-es p.es{display:block}
@media print{body{background:#fff;color:#111}.toggle,.search,.chips{display:none}
.row,.card{border-color:#ccc;background:#fff}.row>summary{background:#fff}}
"""

JS = """
const DATA = __DATA__;
const L = {get(o){return o?(document.body.classList.contains('lang-es')?(o.es||o.en):(o.en||o.es)):''}};
let filter = 'ALL', term = '';
const norm = s => (s||'').normalize('NFKD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();

function itemHtml(fw, it){
  return `<div class="item"><span class="id ${fw}">${it.id}</span>
    <span class="t">${L.get(it.title)}<br><small>${L.get(it.family_title)}</small></span>
    ${it.coverage?`<span class="cov ${it.coverage}">${it.coverage}</span>`:''}
    ${it.source?`<span class="src">${it.source}</span>`:''}</div>`;
}

function rowHtml(r){
  const c = DATA.controls.ISO[r.iso];
  let body = '';
  for (const fw of ['ENS','NIS2','DORA']){
    const items = r[fw] || [];
    body += `<div class="fw"><h4>${fw}</h4>` + (items.length
      ? items.map(i=>itemHtml(fw,i)).join('')
      : `<div class="empty"><span class="en">Nothing equivalent in this framework.</span>
         <span class="es">Sin equivalente en este marco.</span></div>`) + `</div>`;
  }
  const pills = ['ENS','NIS2','DORA'].map(fw =>
    `<span class="cov ${r.cov[fw]}">${fw} ${r.cov[fw]}</span>`).join(' ');
  return `<details class="row"><summary><span class="id ISO">${r.iso}</span>
    <span class="rt">${L.get(c.title)}</span>${pills}</summary>
    <div class="body">${body}</div></details>`;
}

function render(){
  const list = DATA.rows.filter(r => {
    if (filter !== 'ALL' && r.cov[filter] === 'none') return false;
    if (!term) return true;
    return norm(r.blob).includes(norm(term));
  });
  document.getElementById('rows').innerHTML = list.map(rowHtml).join('');
  document.getElementById('count').textContent = list.length + ' / ' + DATA.rows.length;
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('q').addEventListener('input', e => { term = e.target.value; render(); });
  document.querySelectorAll('.chip').forEach(ch => ch.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('on'));
    ch.classList.add('on'); filter = ch.dataset.fw; render();
  }));
  document.querySelectorAll('.toggle button').forEach(b => b.addEventListener('click', () => {
    document.body.classList.toggle('lang-es', b.dataset.lang === 'es');
    document.querySelectorAll('.toggle button').forEach(x =>
      x.classList.toggle('on', x.dataset.lang === b.dataset.lang));
    render();
  }));
  render();
});
"""


def _payload(dataset: Dataset) -> Dict[str, Any]:
    controls = {fw: {c.id: {"title": c.title, "family_title": c.family_title}
                     for c in dataset.all_controls(fw)}
                for fw in ("ISO", "ENS", "NIS2", "DORA")}
    rows = []
    for control in dataset.all_controls("ISO"):
        row: Dict[str, Any] = {"iso": control.id, "cov": dataset.coverage.get(control.id, {})}
        blob = [control.id, control.title.get("en", ""), control.title.get("es", "")]
        for framework in ("ENS", "NIS2", "DORA"):
            items = []
            for link in dataset.forward.get(control.id, {}).get(framework, []):
                target = dataset.control(framework, link.target)
                if not target:
                    continue
                items.append({"id": target.id, "title": target.title,
                              "family_title": target.family_title,
                              "coverage": link.coverage, "source": link.source})
                blob += [target.id, target.title.get("en", ""), target.title.get("es", "")]
            row[framework] = items
        row["blob"] = " ".join(blob)
        rows.append(row)
    return {"controls": controls, "rows": rows}


def render(dataset: Dataset) -> str:
    payload = json.dumps(_payload(dataset), ensure_ascii=False, separators=(",", ":"))
    stats = dataset.stats()
    cards = ""
    for framework in dataset.frameworks:
        fid = framework["id"]
        if fid == "ISO":
            extra = f"{stats['iso_controls']} " + '<span class="en">controls</span><span class="es">controles</span>'
            bar = '<i style="width:100%;background:var(--iso)"></i>'
        else:
            counts = stats[fid]
            total = sum(counts.values()) or 1
            extra = (f"{counts['full']} " + '<span class="en">full</span><span class="es">total</span>'
                     f" · {counts['partial']} " + '<span class="en">partial</span><span class="es">parcial</span>'
                     f" · {counts['none']} " + '<span class="en">none</span><span class="es">ninguna</span>')
            bar = "".join(
                f'<i style="width:{counts[k]*100/total:.1f}%;background:var(--{k})"></i>'
                for k in ("full", "partial", "none"))
        cards += f"""<div class="card"><h3>{fid}</h3>
  <p><span class="en">{framework['kind']['en']}</span><span class="es">{framework['kind']['es']}</span></p>
  <p style="margin-top:6px"><span class="en">{framework['scope']['en']}</span><span class="es">{framework['scope']['es']}</span></p>
  <p style="margin-top:8px">{extra}</p><div class="bar">{bar}</div></div>"""

    gaps = ""
    for framework in ("ENS", "NIS2", "DORA"):
        missing = orphans(dataset, framework)
        if not missing:
            continue
        items = "".join(
            f'<div class="item"><span class="id {framework}">{c.id}</span>'
            f'<span class="t"><span class="en">{c.title.get("en","")}</span>'
            f'<span class="es">{c.title.get("es","")}</span></span></div>'
            for c in missing)
        gaps += f'<div class="fw"><h4>{framework}</h4>{items}</div>'
    gaps_block = f"""<h2><span class="en">What ISO 27001 does not give you</span>
<span class="es">Lo que ISO 27001 no le da</span></h2>
<div class="card"><p style="color:#cfd8e5;font-size:14px;margin-bottom:6px">
<span class="en">Requirements of the other regimes that no ISO 27002 control corresponds to. These are
the ones a certified organisation still has to build from scratch.</span>
<span class="es">Requisitos de los otros regimenes a los que no corresponde ningun control de ISO 27002.
Son los que una organizacion certificada todavia tiene que construir desde cero.</span></p>
{gaps}</div>""" if gaps else ""

    sources = "".join(
        f'<div class="item"><span class="src">{s.id}</span>'
        f'<span class="t"><a href="{s.url}" style="color:var(--accent)">'
        f'<span class="en">{s.title.get("en","")}</span><span class="es">{s.title.get("es","")}</span></a>'
        + (f'<br><small><span class="en">{s.note.get("en","")}</span>'
           f'<span class="es">{s.note.get("es","")}</span></small>' if s.note else "")
        + "</span></div>"
        for s in dataset.sources.values())

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>crossmap — ISO 27001 · ENS · NIS2 · DORA</title>
<style>{CSS}</style></head><body class="lang-es"><div class="wrap">
<header><div><h1>crossmap</h1>
<p class="sub en">Cross-reference between ISO/IEC 27001:2022, the Spanish ENS, NIS2 and DORA,
anchored on the 93 controls of ISO/IEC 27002:2022.</p>
<p class="sub es">Equivalencias entre ISO/IEC 27001:2022, el ENS, NIS2 y DORA, tomando como eje
los 93 controles de ISO/IEC 27002:2022.</p>
<a class="brand" href="https://github.com/mr7security" target="_blank" rel="noopener">
<b>mr7security</b><span class="en">· security tooling</span><span class="es">· herramientas de seguridad</span></a></div>
<div class="toggle"><button data-lang="en">EN</button><button data-lang="es" class="on">ES</button></div>
</header>

<div class="legend">
<p class="en" style="margin:0"><b>NIS2 and DORA are not control catalogues.</b> NIS2 states ten
obligations in Article 21(2) and details them, for some sectors, in Implementing Regulation (EU)
2024/2690; DORA is a regulation with articles and technical standards. So each row says how far an
ISO control takes you towards the obligation — <b>full</b>, <b>partial</b> or <b>none</b> — rather
than pretending there is a one-to-one equivalent.</p>
<p class="es" style="margin:0"><b>NIS2 y DORA no son catalogos de controles.</b> NIS2 enuncia diez
obligaciones en el articulo 21.2 y las detalla, para algunos sectores, en el Reglamento de Ejecucion
(UE) 2024/2690; DORA es un reglamento con articulos y normas tecnicas. Por eso cada fila dice hasta
donde le lleva un control ISO respecto de la obligacion — <b>total</b>, <b>parcial</b> o
<b>ninguna</b> — en lugar de fingir que existe un equivalente uno a uno.</p>
</div>

<div class="grid4">{cards}</div>

<div class="search"><input id="q" type="search"
  placeholder="Buscar: 8.15, registro, cifrado, backup, op.exp.8, art.12, cir.3.2..."></div>
<div class="chips">
  <span class="chip on" data-fw="ALL"><span class="en">All</span><span class="es">Todos</span></span>
  <span class="chip" data-fw="ENS"><span class="en">With ENS correspondence</span><span class="es">Con equivalencia ENS</span></span>
  <span class="chip" data-fw="NIS2"><span class="en">With NIS2 correspondence</span><span class="es">Con equivalencia NIS2</span></span>
  <span class="chip" data-fw="DORA"><span class="en">With DORA correspondence</span><span class="es">Con equivalencia DORA</span></span>
</div>
<p class="count"><span id="count"></span> <span class="en">controls shown</span><span class="es">controles mostrados</span></p>
<div id="rows"></div>

{gaps_block}

<h2><span class="en">Sources</span><span class="es">Fuentes</span></h2>
<div class="card">{sources}</div>

<footer>
<p class="en">Every correspondence in this dataset is a reading, not a legal statement, and is marked
as proposed until confirmed against the cited document. Generated by crossmap.</p>
<p class="es">Cada correspondencia de este conjunto de datos es una lectura, no una afirmacion
juridica, y consta como propuesta mientras no se confirme contra el documento citado. Generado con
crossmap.</p>
<a class="brand" href="https://github.com/mr7security" target="_blank" rel="noopener">
<b>mr7security</b><span class="en">· Miguel David Rebolledo Romero</span>
<span class="es">· Miguel David Rebolledo Romero</span></a>
</footer></div>
<script>{JS.replace("__DATA__", payload)}</script>
</body></html>"""
