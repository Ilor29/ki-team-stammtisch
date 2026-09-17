"""KRUG//STAMMTISCH — Web-Dienst. Lauscht nur auf 127.0.0.1:8806, Caddy davor
(Passwort = Leitstand). Seiten unter /, Schnittstelle unter /api/."""
import pathlib, json, re, subprocess, time, os, zipfile, io, urllib.parse, urllib.request, secrets
from collections import deque
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import motor

HIER = pathlib.Path(__file__).parent.parent
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.on_event("startup")
def _wiederaufnehmen():
    n = motor.wiederaufnehmen()
    if n: print(f"Stammtisch: {n} unterbrochene Runde(n) fortgesetzt", flush=True)

class Start(BaseModel):
    thema: str
    teilnehmer: list[str] = ["sepp", "julia", "greta", "timo", "david", "sven", "basti", "fine", "xaver"]
    runden: int | None = None
    anhaenge: list[str] = []      # IDs hochgeladener Unterlagen

class Text(BaseModel):
    text: str = ""
    anhaenge: list[str] = []

# ---- Diktat glaetten: wie in der Relay-App, ueber Rolis Abo (claude -p, Haiku), mit Kostenbremse ----
_GLAETTEN_PROMPT = ("Du glaettest einen diktierten deutschen Text fuer eine Besprechung. Entferne Fuellwoerter (aehm, aeh, halt) "
    "und Wortdopplungen, behebe offensichtliche Versprecher und Verhoerer aus dem Zusammenhang, setze Satzzeichen und "
    "Grossschreibung. Bewahre Sinn und Absicht des Sprechers; erfinde nichts dazu und beantworte den Text NICHT. "
    "Gib ausschliesslich den bereinigten Text zurueck, ohne Anfuehrungszeichen, ohne Vorrede, ohne Erklaerung.")
_glaett_rufe: deque = deque()
def _glaetten_erlaubt():
    jetzt = time.time()
    while _glaett_rufe and _glaett_rufe[0] < jetzt - 60: _glaett_rufe.popleft()
    if len(_glaett_rufe) >= 12: return False
    _glaett_rufe.append(jetzt); return True

def _glaetten(text):
    r = subprocess.run(["claude", "-p", "--model", "haiku", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                        "--no-session-persistence", "--max-turns", "1", "--tools", "", "--effort", "low", "--settings", motor.ABO_EINSTELLUNGEN, "--output-format", "text"],
                       input=_GLAETTEN_PROMPT + "\n\nText: " + text, capture_output=True, text=True, timeout=45, env=motor.cron_umgebung(), cwd="/home/BENUTZER")
    if r.returncode != 0: raise RuntimeError(r.stderr[-200:])
    return r.stdout.strip()

@app.post("/api/glaetten")
def glaetten(t: Text):
    text = t.text.strip()
    if not text: return {"text": ""}
    if not _glaetten_erlaubt(): raise HTTPException(429, "Zu viele Glaett-Anfragen kurz hintereinander, kurz warten.")
    try: sauber = _glaetten(text)
    except subprocess.TimeoutExpired: raise HTTPException(504, "Das Glaetten hat zu lange gedauert, bitte nochmal.")
    except Exception: raise HTTPException(502, "Das Glaetten hat gerade nicht geklappt.")
    return {"text": sauber or text}

# ---- Unterlagen an den Tisch legen: Datei kommt roh im Body, Name im Kopf X-Dateiname ----
def _xml_text(daten):
    t = re.sub(r"</(w:p|text:p|a:p|p)>", "\n", daten.decode("utf-8", "replace"))
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\n{3,}", "\n\n", t)

def _text_aus(name, daten):
    endung = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    if endung == "pdf":
        r = subprocess.run(["pdftotext", "-layout", "-", "-"], input=daten, capture_output=True, timeout=60)
        return r.stdout.decode("utf-8", "replace")
    if endung in ("docx", "odt", "pptx", "xlsx"):
        with zipfile.ZipFile(io.BytesIO(daten)) as z:
            namen = [n for n in z.namelist() if n in ("word/document.xml", "content.xml", "xl/sharedStrings.xml") or n.startswith("ppt/slides/slide")]
            return "\n".join(_xml_text(z.read(n)) for n in sorted(namen))
    return daten.decode("utf-8", "replace")

def _bild_text(pfad):
    auftrag = (f"Lies die Bilddatei {pfad.name} im aktuellen Ordner mit dem Read-Werkzeug. Gib ihren Inhalt als Text wieder: "
               "Steht Text darauf (Dokument, Etikett, Tabelle, Notiz), schreib ihn vollstaendig ab. Zeigt es etwas anderes, "
               "beschreibe knapp und sachlich, was zu sehen ist. Nur der Inhalt, keine Vorrede.")
    r = subprocess.run(["claude", "-p", auftrag, "--model", "haiku", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                        "--allowedTools", f"Read({motor.ANHAENGE}/**)", "--permission-prompts", "none", "--max-turns", "4", "--effort", "low",
                        "--no-session-persistence", "--settings", motor.ABO_EINSTELLUNGEN, "--output-format", "text"],
                       capture_output=True, text=True, timeout=120, env=motor.cron_umgebung(), cwd=str(motor.ANHAENGE), stdin=subprocess.DEVNULL)
    if r.returncode != 0: raise RuntimeError(r.stderr[-200:])
    return r.stdout.strip()

@app.post("/api/anhang")
async def anhang(request: Request):
    name = urllib.parse.unquote(request.headers.get("x-dateiname") or "Unterlage")
    name = re.sub(r"[\\/]", "_", name)[:120]
    daten = await request.body()
    if len(daten) > 15_000_000: raise HTTPException(413, "Die Datei ist zu gross (mehr als 15 MB).")
    aid = time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3)
    endung = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    if endung in ("jpg", "jpeg", "png", "webp", "gif", "heic", "heif"):
        # Foto oder Kamerabild: eine Persona kann es nicht direkt sehen, also liest das Abo-Modell es vor
        pfad = motor.ANHAENGE / f"{aid}.{endung}"; pfad.write_bytes(daten)
        try: text = _bild_text(pfad)
        except Exception: text = ""
        if not text: raise HTTPException(415, "Das Bild liess sich nicht lesen. Bitte nochmal versuchen oder als PDF schicken.")
    else:
        try: text = _text_aus(name, daten)
        except Exception: raise HTTPException(415, "Aus dieser Datei laesst sich kein Text lesen.")
    text = re.sub(r"[ \t]+\n", "\n", text).strip()[:60000]
    if not text: raise HTTPException(415, "In der Datei steht kein lesbarer Text (bei PDF: nur Bild?).")
    (motor.ANHAENGE / f"{aid}.json").write_text(json.dumps({"id": aid, "name": name, "text": text, "zeichen": len(text), "zeit": time.strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False))
    return {"id": aid, "name": name, "zeichen": len(text), "vorschau": text[:160]}

@app.post("/api/start")
def start(s: Start, request: Request):
    if not s.thema.strip():
        raise HTTPException(400, "Thema fehlt.")
    laufende = [r for r in motor.AKTIV.values() if r.status in ("läuft", "pause")]
    if laufende:
        raise HTTPException(409, "Es läuft schon eine Runde. Erst beenden oder abwarten.")
    n = (request.headers.get("x-nutzer") or "BENUTZER").strip().lower()
    r = motor.starten(s.thema, s.teilnehmer, s.runden, {"anna": "Anna", "ben": "Ben"}.get(n, n.capitalize()), s.anhaenge[:6])
    return r.zustand()

@app.get("/api/wer")
def wer(request: Request):
    n = (request.headers.get("x-nutzer") or "BENUTZER").strip().lower()
    return {"nutzer": n, "name": {"anna": "Anna", "ben": "Ben"}.get(n, n.capitalize())}

def _wer(request: Request):
    n = (request.headers.get("x-nutzer") or "BENUTZER").strip().lower()
    return {"anna": "Anna", "ben": "Ben"}.get(n, n.capitalize())

@app.get("/api/runden")
def runden(request: Request): return motor.alle(_wer(request))

@app.get("/api/runde/{rid}")
def runde(rid: str, request: Request):
    z = motor.laden(rid)
    if not z: raise HTTPException(404, "Runde nicht gefunden.")
    wer = _wer(request)
    if wer != "Roli" and (z.get("gastgeber") or "Roli") != wer: raise HTTPException(404, "Runde nicht gefunden.")
    return z

@app.post("/api/runde/{rid}/einwurf")
def einwurf(rid: str, t: Text, request: Request):
    r = motor.AKTIV.get(rid)
    if not r or r.status not in ("läuft", "pause"): raise HTTPException(409, "Diese Runde läuft nicht mehr.")
    n = (request.headers.get("x-nutzer") or "BENUTZER").strip().lower()
    if not t.text.strip() and not t.anhaenge: raise HTTPException(400, "Einwurf ist leer.")
    r.einwurf(t.text.strip()[:600], {"anna": "Anna", "ben": "Ben"}.get(n, n.capitalize()), t.anhaenge[:4]); return {"ok": True}

@app.post("/api/runde/{rid}/nachfrage")
def nachfrage(rid: str, t: Text, request: Request):
    """Roli fragt bei einer fertigen Runde nach: eine weitere Runde zu seinem Punkt."""
    if not t.text.strip(): raise HTTPException(400, "Nachfrage ist leer.")
    if [r for r in motor.AKTIV.values() if r.status in ("läuft", "pause")]:
        raise HTTPException(409, "Es läuft schon eine Runde. Erst beenden oder abwarten.")
    z = motor.laden(rid); wer = _wer(request)
    if z and wer != "Roli" and (z.get("gastgeber") or "Roli") != wer: raise HTTPException(404, "Runde nicht gefunden.")
    try: r = motor.nachfragen(rid, t.text.strip()[:600], wer)
    except RuntimeError as e: raise HTTPException(409, str(e))
    if not r: raise HTTPException(404, "Runde nicht gefunden.")
    return r.zustand()

@app.delete("/api/runde/{rid}")
def loeschen(rid: str, request: Request):
    z = motor.laden(rid); wer = _wer(request)
    if z and wer != "Roli" and (z.get("gastgeber") or "Roli") != wer: raise HTTPException(404, "Runde nicht gefunden.")
    try: ok = motor.loeschen(rid)
    except RuntimeError as e: raise HTTPException(409, str(e))
    if not ok: raise HTTPException(404, "Runde nicht gefunden.")
    return {"ok": True}

@app.post("/api/runde/{rid}/glocke")
def glocke(rid: str):
    r = motor.AKTIV.get(rid)
    if not r or r.status not in ("läuft", "pause"): raise HTTPException(409, "Diese Runde läuft nicht mehr.")
    r.pause = not r.pause; r.status = "pause" if r.pause else "läuft"; r.speichern()
    return {"pause": r.pause}

@app.post("/api/runde/{rid}/stop")
def stop(rid: str):
    r = motor.AKTIV.get(rid)
    if not r: raise HTTPException(404, "Runde nicht gefunden.")
    r.stop = True; r.pause = False; return {"ok": True}

@app.post("/api/sprich")
async def sprich(request: Request):
    """Liest einen Beitrag mit der Hausstimme vor.

    Roli am 16.09.2026: „manchmal sind die Dialoge sehr lang, was für mich Lesen sehr anstrengend
    ist ... wenn man das einfach über die Piper-Stimme vorlesen lassen kann." Der Vorleser läuft
    ohnehin auf 127.0.0.1:5005 für die Relay-App; wir reichen nur weiter, nichts Neues installiert.

    Der Name des Sprechers wird mitgesprochen. Es gibt nur eine deutsche Stimme, deshalb ist das
    Gesagte die einzige Möglichkeit zu hören, wer gerade dran ist.
    """
    d = await request.json()
    text = (d.get("text") or "").strip()
    wer = (d.get("wer") or "").strip()
    if not text:
        raise HTTPException(400, "Kein Text")
    if len(text) > 3000:
        text = text[:3000]
    ansage = (wer + ". ") if wer else ""
    try:
        anfrage = urllib.request.Request(
            "http://127.0.0.1:5005/",
            data=json.dumps({"text": ansage + text}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(anfrage, timeout=120) as antwort:
            ton = antwort.read()
    except Exception as e:
        raise HTTPException(503, f"Vorleser antwortet nicht: {type(e).__name__}")
    return Response(content=ton, media_type="audio/wav",
                    headers={"Cache-Control": "no-store"})


@app.get("/pdf/{name}")
def pdf(name: str):
    p = motor.DATEN.parent / "Downloads" / "Stammtisch" / name
    if not p.exists() or not name.endswith(".pdf") or "/" in name: raise HTTPException(404, "PDF nicht gefunden.")
    return FileResponse(p, media_type="application/pdf", filename=name)

app.mount("/", StaticFiles(directory=HIER / "web", html=True), name="web")

def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8806, log_level="warning")

if __name__ == "__main__":
    main()
