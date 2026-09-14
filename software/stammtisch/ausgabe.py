"""Protokoll-Ausgabe: Markdown ins Zweitgehirn (Firmenwissen/12 Stammtisch) und ein
PDF im FELD//PULS-Look nach ~/Downloads/Stammtisch/. Das PDF druckt der kopflose
Chromium des Browser-Prüfers."""
import html, pathlib, re, subprocess, time, markdown

AUSGABE = pathlib.Path("/home/BENUTZER/Downloads/Stammtisch"); AUSGABE.mkdir(parents=True, exist_ok=True)
STIL = """@page{size:A4;margin:22mm 18mm}body{font-family:'IBM Plex Sans','Segoe UI',system-ui,sans-serif;color:#1a1a1a;line-height:1.55;font-size:10.5pt}
h1{font-size:19pt;color:#0F152A;border-bottom:3px solid #FF910B;padding-bottom:6px}h2{font-size:13pt;color:#0F152A;margin-top:20px;border-left:5px solid #FF910B;padding-left:8px;page-break-after:avoid}
.beitrag{margin:9px 0;padding:6px 10px;border-left:3px solid #ddd}.beitrag b{color:#0F152A}.einwurf{border-left-color:#2E8B57;background:#F1FAF4}.fazit{border-left-color:#FF910B;background:#FFF8EA}
.meta{color:#666;font-size:9pt}.fuss{margin-top:30px;font-size:8.5pt;color:#888;border-top:1px solid #ddd;padding-top:6px}"""

def dateiname(r):
    kurz = re.sub(r"[^a-zA-Z0-9äöüÄÖÜß ]+", "", r.thema)[:50].strip().replace(" ", "-") or "Runde"
    return f"{r.id[:8]}-{kurz}"

def markdown_text(r):
    z = ["---", f"titel: Stammtisch {r.id[:8]} — {r.thema}", "typ: protokoll", "tags: [stammtisch, ki-team]",
         f"stand: {time.strftime('%Y-%m-%d')}", "---", "", f"# KRUG//STAMMTISCH — {r.thema}", "",
         f"> Runde vom {r.id[6:8]}.{r.id[4:6]}.{r.id[:4]} um {r.id[9:11]}:{r.id[11:13]} Uhr · Teilnehmer: "
         + ", ".join(r.teilnehmer) + f" · {r.runden} Runden · KI-Gespräch, Fakten vor Verwendung prüfen.", ""]
    for e in r.eintraege:
        kopf = "**Roland (Einwurf):**" if e["art"] == "einwurf" else (f"**{e['name']} · Fazit:**" if e["art"] == "fazit" else f"**{e['name']} ({e['rolle']}):**")
        z.append(f"{kopf} {e['text']}\n")
    return "\n".join(z)

def pdf_und_notiz(r):
    md = markdown_text(r)
    subprocess.run(["python3", "/home/BENUTZER/.notizen-schreiben.py", f"06 Firmenwissen/12 Stammtisch/{dateiname(r)}.md"],
                   input=md, text=True, capture_output=True)
    teile = [f"<h1>KRUG//STAMMTISCH — {html.escape(r.thema)}</h1>",
             f"<p class='meta'>Runde vom {r.id[6:8]}.{r.id[4:6]}.{r.id[:4]}, {r.id[9:11]}:{r.id[11:13]} Uhr · Teilnehmer: {html.escape(', '.join(r.teilnehmer))} · {r.runden} Runden</p>"]
    for e in r.eintraege:
        kl = "einwurf" if e["art"] == "einwurf" else ("fazit" if e["art"] == "fazit" else "")
        wer = "Roland (Einwurf)" if e["art"] == "einwurf" else (f"{e['name']} · Fazit" if e["art"] == "fazit" else f"{e['name']} ({e['rolle']})")
        teile.append(f"<div class='beitrag {kl}'><b>{html.escape(wer)}</b> <span class='meta'>{e['zeit']}</span><br>{html.escape(e['text'])}</div>")
    teile.append("<div class='fuss'>Masskrugflasche GmbH — internes Gesprächsprotokoll des KI-Teams (KRUG//STAMMTISCH), erstellt mit KI-Unterstützung. Zahlen ohne Quelle sind Einschätzungen.</div>")
    seite = f"<!doctype html><html lang='de'><head><meta charset='utf-8'><style>{STIL}</style></head><body>{''.join(teile)}</body></html>"
    hp = AUSGABE / (dateiname(r) + ".html"); hp.write_text(seite)
    pp = AUSGABE / (dateiname(r) + ".pdf")
    skript = f"""from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.goto('file://{hp}'); pg.wait_for_timeout(500)
    pg.pdf(path='{pp}', format='A4', print_background=True); b.close()"""
    subprocess.run(["/home/BENUTZER/werkzeuge/browser/.venv/bin/python", "-c", skript], capture_output=True, timeout=120)
    hp.unlink(missing_ok=True)
    try:
        subprocess.run(["/home/BENUTZER/.ereignis.sh", "stammtisch", "Runde beendet", f"{r.thema[:80]} ({len(r.eintraege)} Beiträge, {r.tokens} Tokens)", "done"])
    except Exception: pass
    return pp.name if pp.exists() else None
