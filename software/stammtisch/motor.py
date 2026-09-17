"""Der Runden-Motor: lässt die Personas reihum sprechen, nimmt Rolis Einwürfe auf,
hält bei der Glocke an und schließt mit Sepps Fazit. Modelle über OpenRouter
(Schlüssel aus ~/.hermes/.env), Runden günstig, Fazit stark."""
import json, pathlib, re, threading, time, urllib.request
from . import wissen

DATEN = pathlib.Path("/home/BENUTZER/stammtisch-daten"); RUNDEN = DATEN / "runden"; RUNDEN.mkdir(parents=True, exist_ok=True)
KONFIG = DATEN / "config.json"
ANHAENGE = DATEN / "anhaenge"; ANHAENGE.mkdir(exist_ok=True)   # hochgeladene Unterlagen (Text-Auszug)
STANDARD = {"modus": "abo",                      # abo = Claude Code über Rolis Abo (Netz + Zweitgehirn), openrouter = Notnagel
            "abo_modell_runde": "sonnet", "abo_modell_fazit": "opus",
            "modell_runde": "anthropic/claude-haiku-4.5", "modell_fazit": "anthropic/claude-sonnet-5",
            "max_saetze": 3, "runden": 2}
PROFILE = {"sepp": "sepp-koordination", "julia": "julia-werberecht", "greta": "greta-finanzen",
           "timo": "timo-marketing", "david": "david-exportrecht", "sven": "sven-logistik",
           "basti": "basti-vertrieb", "fine": "fine-design", "xaver": "xaver-technik"}
NAMEN = {"sepp": "Sepp", "julia": "Julia", "greta": "Greta", "timo": "Timo", "david": "David", "sven": "Sven", "basti": "Basti", "fine": "Fine", "xaver": "Xaver"}
ROLLEN = {"sepp": "Koordination", "julia": "Werberecht", "greta": "Finanzen", "timo": "Marketing",
          "david": "Export", "sven": "Logistik", "basti": "Vertrieb", "fine": "Design", "xaver": "Technik"}

def konfig():
    k = dict(STANDARD)
    if KONFIG.exists():
        try: k.update(json.loads(KONFIG.read_text()))
        except Exception: pass
    return k

def schluessel():
    orte = [pathlib.Path("/home/BENUTZER/.stammtisch-schluessel"), pathlib.Path("/home/BENUTZER/.hermes/.env")]
    orte += sorted(pathlib.Path("/home/BENUTZER/.hermes/profiles").glob("*/.env"))
    for p in orte:
        if not p.exists(): continue
        for zeile in p.read_text().splitlines():
            if zeile.startswith("OPENROUTER_API_KEY="):
                return zeile.split("=", 1)[1].strip()
    raise RuntimeError("Kein OpenRouter-Schlüssel gefunden (~/.stammtisch-schluessel oder Hermes-Umgebung)")

VERZEICHNIS = pathlib.Path.home() / "projekte/agenten-liste/PERSONALVERZEICHNIS.md"
FACHKRAEFTE = pathlib.Path.home() / ".hermes/fachkraefte"
def fachkraefte_liste():
    """{id: (Kurzname, Satz, Abteilung)} aus dem Personalverzeichnis."""
    aus, abt = {}, ""
    if not VERZEICHNIS.exists(): return aus
    for z in VERZEICHNIS.read_text().splitlines():
        if z.startswith("## "): abt = re.sub(r"\s*\(\d+\)", "", z[3:]).strip()
        m = re.match(r"- ([a-z0-9-]+): ([^.]+)\.\s*(.*)", z)
        if m: aus[m.group(1)] = (m.group(2).strip(), m.group(3).strip(), abt)
    return aus

PORTRAETS = pathlib.Path(__file__).resolve().parent.parent / "web" / "stammtisch" / "fk"
WERKSTATT = pathlib.Path.home() / "projekte/Medienwerk/werkzeuge/kie-werkstatt.sh"

def fachkraft_portraet(fid, name, abteilung):
    """Rundes Portraet im Stil der Leiter (nano-banana-2-lite, 4 Credits), einmalig je Fachkraft, Ablage web/stammtisch/fk/<id>.png.
    Aussehen wird aus der Kennung abgeleitet, damit es stabil bleibt und die Fachkraefte sich unterscheiden."""
    import subprocess, hashlib
    PORTRAETS.mkdir(parents=True, exist_ok=True)
    ziel = PORTRAETS / f"{fid}.png"
    if ziel.exists() or not WERKSTATT.exists(): return ziel.exists()
    h = int(hashlib.md5(fid.encode()).hexdigest(), 16)
    person = ["man", "woman"][h % 2]
    alter = ["early thirties", "late thirties", "mid forties", "early fifties"][(h >> 2) % 4]
    haar = {"man": ["short dark hair", "short grey hair", "short curly brown hair", "shaved head", "dark blond hair, trimmed beard"],
            "woman": ["shoulder-length dark hair", "short blond hair", "curly brown hair tied back", "grey bob", "long auburn hair"]}[person][(h >> 5) % 5]
    kleid = ["dark green shirt", "grey blazer over a black shirt", "rust-coloured knit sweater", "white blouse with rolled sleeves", "navy cardigan", "denim shirt"][(h >> 9) % 6]
    art = "creative, attentive" if any(k in abteilung for k in ("Marketing", "Design", "Vertrieb")) else "calm, analytical"
    prompt = (f"Painterly photorealistic chest-up portrait of a {art} German {person} in the {alter}, {haar}, {kleid}, "
              f"working as {name}, small confident smile, warm amber side light, plain warm grey studio background, editorial team portrait, looking at camera, square")
    try:
        subprocess.run([str(WERKSTATT), "erzeuge", "--modell", "nano-banana-2-lite", "--typ", "bild", "--projekt", f"team-fk-{fid}",
                        "--prompt", prompt, "--input", json.dumps({"prompt": prompt, "aspect_ratio": "1:1"}),
                        "--marke", "Krugmeister", "--fach", "Bilder", "--von", "Stammtisch", "--quelle", "automatisch"],
                       capture_output=True, text=True, timeout=420, cwd=str(pathlib.Path.home()))
    except Exception:
        pass   # Zeitgrenze: das Bild kann trotzdem fertig geworden sein, unten wird nachgesehen
    return runden_und_ablegen(fid)

def runden_und_ablegen(fid):
    """Neuestes Bild aus dem Medien-Ordner der Fachkraft rund zuschneiden und als Portraet ablegen."""
    ziel = PORTRAETS / f"{fid}.png"
    if ziel.exists(): return True
    ordner = sorted((pathlib.Path.home() / "Medien").glob(f"*team-fk-{fid}"), reverse=True)
    bild = next((q for o in ordner for q in sorted(o.glob("*.jp*g"), reverse=True)), None)
    if not bild: return False
    try:
        from PIL import Image, ImageDraw
        PORTRAETS.mkdir(parents=True, exist_ok=True)
        im = Image.open(bild).convert("RGBA"); w, h2 = im.size; m = min(w, h2)
        im = im.crop(((w - m) // 2, (h2 - m) // 2, (w - m) // 2 + m, (h2 - m) // 2 + m)).resize((320, 320))
        maske = Image.new("L", (320, 320), 0); ImageDraw.Draw(maske).ellipse((0, 0, 319, 319), fill=255); im.putalpha(maske)
        im.save(ziel); return True
    except Exception:
        return False

def fachkraft_anmelden(fid):
    """Fachkraft als Sprecher registrieren (Name und Rolle fuer Protokoll und Buehne)."""
    kurz = "fk:" + fid; info = fachkraefte_liste().get(fid)
    if not info: return None
    NAMEN[kurz] = info[0]; ROLLEN[kurz] = "Fachkraft " + info[2]
    return kurz

def seele(kurz):
    if kurz.startswith("fk:"):
        fp = FACHKRAEFTE / (kurz[3:] + ".md")
        rolle = fp.read_text()[:7000] if fp.exists() else ""
        return (f"Du bist {NAMEN.get(kurz, kurz)}, eine Fachkraft auf Zeit am KRUG//STAMMTISCH ({ROLLEN.get(kurz, 'Fachkraft')}). "
                "Du sprichst Deutsch, in ganzen Saetzen, ohne Listen und ohne Englisch-Fachjargon, und bringst genau das Fachwissen deiner Rolle ein, "
                "bezogen auf Rolis Haus und das Thema; alles andere ueberlaesst du den Abteilungsleitern.\n\n## Deine Rolle (Vorlage)\n" + rolle)
    p = pathlib.Path.home() / ".hermes" / "profiles" / PROFILE[kurz] / "SOUL.md"
    t = p.read_text() if p.exists() else f"Du bist {NAMEN[kurz]} ({ROLLEN[kurz]})."
    # Tafel-Anweisungen gelten hier nicht
    t = re.sub(r"- Zusammenarbeit über die Kanban-Tafel.*?\n(?:\s{2,}.*\n)*", "", t)
    return t

ABO_EINSTELLUNGEN = '{"disableAllHooks":true,"enabledPlugins":{"roli-koffer@koffer":false}}'

def cron_umgebung():
    """Umgebung für kopflose Aufrufe: fester HOME/PATH, kein Terminal-Titel, und das Jahres-Token
    aus ~/.claude-cron-token, falls Roli es mit `claude setup-token` hinterlegt hat."""
    import os
    u = dict(os.environ, HOME="/home/BENUTZER", PATH="/home/BENUTZER/.local/bin:/usr/local/bin:/usr/bin:/bin",
             CLAUDE_CODE_DISABLE_TERMINAL_TITLE="1")
    try:
        for zeile in (pathlib.Path.home() / ".claude-cron-token").read_text().splitlines():
            if zeile.startswith("CLAUDE_CODE_OAUTH_TOKEN=") and zeile.split("=", 1)[1].strip():
                u["CLAUDE_CODE_OAUTH_TOKEN"] = zeile.split("=", 1)[1].strip()
    except OSError:
        pass
    return u

def anfrage_abo(modell, system, nutzer, aufwand="medium", max_zuege=8, zeit=240):
    """Redebeitrag über Rolis Claude-Abo: claude -p mit der Persona als System-Zusatz (aus Datei,
    weil lange Seelen plus Unterlagen die Argument-Grenze sprengen können). Die Persona darf lesen
    (Firmenwissen) und im Netz suchen, sonst nichts; keine Hooks, kein Koffer-Stil, keine Sitzung
    auf der Platte, höchstens acht Züge."""
    import subprocess, tempfile, json
    with tempfile.NamedTemporaryFile("w", suffix=".md", prefix="seele-", delete=False) as f:
        f.write(system); seele_datei = f.name
    befehl = ["claude", "-p", nutzer, "--model", modell, "--append-system-prompt-file", seele_datei,
              "--allowedTools", "WebSearch,WebFetch,Read(/home/BENUTZER/Notizen/06 Firmenwissen/**)",
              "--permission-prompts", "none", "--max-turns", str(max_zuege), "--no-session-persistence", "--effort", aufwand,
              "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--settings", ABO_EINSTELLUNGEN,
              "--output-format", "json"]
    try:
        r = subprocess.run(befehl, capture_output=True, text=True, timeout=zeit, cwd="/home/BENUTZER/Notizen/06 Firmenwissen",
                           env=cron_umgebung(), stdin=subprocess.DEVNULL)
    finally:
        pathlib.Path(seele_datei).unlink(missing_ok=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("Abo-Aufruf fehlgeschlagen: " + (r.stderr.strip()[-200:] or "leere Antwort"))
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return r.stdout.strip(), {"total_tokens": 0}
    if d.get("is_error") or not (d.get("result") or "").strip():
        raise RuntimeError("Abo-Aufruf meldet Fehler: " + str(d.get("result", ""))[:200])
    u = d.get("usage") or {}
    return d["result"].strip(), {"total_tokens": int(u.get("input_tokens", 0) or 0) + int(u.get("output_tokens", 0) or 0),
                                 "kosten_usd": d.get("total_cost_usd", 0), "zuege": int(d.get("num_turns", 1) or 1)}

def anfrage(modell, system, nachrichten, max_tokens=700):
    daten = json.dumps({"model": modell, "max_tokens": max_tokens,
                        "messages": [{"role": "system", "content": system}] + nachrichten}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=daten,
        headers={"Authorization": "Bearer " + schluessel(), "Content-Type": "application/json",
                 "HTTP-Referer": "https://DEIN-COCKPIT.example.org", "X-Title": "KRUG//STAMMTISCH"})
    with urllib.request.urlopen(req, timeout=120) as a:
        antwort = json.load(a)
    text = antwort["choices"][0]["message"]["content"].strip()
    kosten = antwort.get("usage", {})
    return text, kosten

def anhang_laden(aid):
    p = ANHAENGE / f"{aid}.json"
    if not re.fullmatch(r"[0-9A-Za-z_-]+", aid or "") or not p.exists(): return None
    try: return json.loads(p.read_text())
    except Exception: return None

WAECHTER_SCHEMA = json.dumps({"type": "object", "properties": {"befund": {"type": "string", "enum": ["ok", "unbelegt"]},
    "stellen": {"type": "array", "items": {"type": "string"}}}, "required": ["befund", "stellen"]})
WAECHTER_REGEL = ("Du bist der Fakten-Waechter am Stammtisch. Pruefe den Redebeitrag: Enthaelt er Tatsachenbehauptungen "
    "(Gesetze, Paragrafen, Verordnungen, Zahlen, Preise, Daten, Eigenschaften von Produkten, Firmen, Personen oder Marken), "
    "die KEINE Herkunft tragen? Als Herkunft gelten: (Firmenwissen: ...), (Quelle: ...), (Tischvorlage) oder eine Kennzeichnung "
    "wie 'nach meiner Einschaetzung', 'ich schaetze', 'vermutlich'. Meinungen, Vorschlaege, Fragen und Erfahrungssaetze sind keine "
    "Tatsachenbehauptungen. Antworte NUR als JSON: befund 'ok' oder 'unbelegt', stellen = die unbelegten Behauptungen woertlich, hoechstens vier.")

def waechter(text):
    """Haiku prueft einen Beitrag auf unbelegte Tatsachen. Gibt die Liste der Stellen zurueck (leer = ok)."""
    import subprocess
    r = subprocess.run(["claude", "-p", "Redebeitrag:\n" + text, "--model", "haiku", "--effort", "low", "--tools", "", "--max-turns", "1",
                        "--no-session-persistence", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--settings", ABO_EINSTELLUNGEN,
                        "--append-system-prompt", WAECHTER_REGEL, "--output-format", "json", "--json-schema", WAECHTER_SCHEMA],
                       capture_output=True, text=True, timeout=90, cwd="/home/BENUTZER", env=cron_umgebung(), stdin=subprocess.DEVNULL)
    try:
        d = json.loads(r.stdout); erg = d.get("structured_output") or json.loads(d.get("result") or "{}")
        return [str(x)[:160] for x in erg.get("stellen", [])] if erg.get("befund") == "unbelegt" else []
    except Exception:
        return []

def herkunft_pruefen(text, vorlage_da):
    """Feste Pruefungen ohne Modell: (Firmenwissen: X) muss eine Notiz sein, die es gibt; (Tischvorlage) nur, wenn es eine gibt."""
    stellen = []
    wurzel = pathlib.Path("/home/BENUTZER/Notizen/06 Firmenwissen")
    stems = [q.stem.lower() for q in wurzel.rglob("*.md")]
    for m in re.finditer(r"\(Firmenwissen:\s*([^)]+)\)", text):
        name = m.group(1).strip().lower()
        if not any(name in st or st in name for st in stems):
            stellen.append("Firmenwissen-Notiz nicht gefunden: " + m.group(1).strip()[:60])
    if not vorlage_da and re.search(r"\(Tischvorlage", text):
        stellen.append("beruft sich auf eine Tischvorlage, die es in dieser Runde nicht gibt")
    return stellen

def kuerzen(text, max_woerter):
    """Roli, 10.09.: die Texte sind zu lang. Ganze Saetze behalten, bis die Wortgrenze erreicht ist."""
    saetze = re.split(r"(?<=[.!?])\s+", text.strip())
    aus, n = [], 0
    for satz in saetze:
        w = len(satz.split())
        if aus and n + w > max_woerter: break
        aus.append(satz); n += w
    return " ".join(aus)

class Runde:
    def __init__(self, thema, teilnehmer, runden=None, gastgeber="Roli", anhaenge=None):
        k = konfig()
        self.id = time.strftime("%Y%m%d-%H%M%S")
        self.thema = thema.strip(); self.gastgeber = gastgeber
        self.teilnehmer = [t for t in ["sepp", "julia", "greta", "timo", "david", "sven", "basti", "fine", "xaver"] if t in teilnehmer] or ["sepp", "greta", "timo"]
        if "sepp" not in self.teilnehmer: self.teilnehmer.insert(0, "sepp")
        self.runden = max(1, min(4, runden or k["runden"]))
        self.eintraege = []      # {wer, name, rolle, text, zeit, art}
        self.status = "läuft"    # läuft | pause | fertig | fehler
        self.einwuerfe = []      # noch nicht beantwortete Einwürfe
        self.pause = False
        self.stop = False
        self.aktuell = None      # wer gerade denkt
        self.tokens = 0
        self.pdf = None
        self.fehler = None
        self.weg = None; self.notiz_fehler = None
        self.fachkraefte = []       # Fachkraefte auf Zeit (kurz 'fk:<id>'), waehlt Sepp
        self.wissen = wissen.auszug(self.thema)
        self.anhaenge = [a for a in (anhang_laden(x) for x in (anhaenge or [])) if a]   # mitgebrachte Unterlagen
        self.speichern()

    def pfad(self): return RUNDEN / f"{self.id}.json"
    def speichern(self):
        self.pfad().write_text(json.dumps(self.zustand(), ensure_ascii=False, indent=1))
    def zustand(self):
        return {"id": self.id, "thema": self.thema, "teilnehmer": self.teilnehmer, "runden": self.runden,
                "status": self.status, "aktuell": self.aktuell, "eintraege": self.eintraege,
                "gastgeber": self.gastgeber, "tokens": self.tokens, "pdf": self.pdf, "fehler": self.fehler, "weg": getattr(self, "weg", None), "offene_einwuerfe": len(self.einwuerfe),
                "anhaenge": [a["name"] for a in getattr(self, "anhaenge", [])], "fachkraefte": [{"kurz": f, "name": NAMEN.get(f, f), "rolle": ROLLEN.get(f, ""), "bild": (f"stammtisch/fk/{f[3:]}.png" if ((PORTRAETS / f"{f[3:]}.png").exists() or runden_und_ablegen(f[3:])) else "stammtisch/gast.png")} for f in getattr(self, "fachkraefte", [])]}

    def eintrag(self, wer, text, art="rede"):
        e = {"wer": wer, "name": NAMEN.get(wer, "Roli"), "rolle": ROLLEN.get(wer, "Gastgeber"),
             "text": text, "zeit": time.strftime("%H:%M"), "art": art}
        if (wer in NAMEN or wer.startswith("fk:")) and art in ("rede", "fazit"):
            e["nachgesehen"] = getattr(self, "letzte_zuege", 1) > 1
            if getattr(self, "letzte_waechter", []): e["waechter"] = self.letzte_waechter
        if wer == "vorlage": e["name"] = "Tischvorlage"; e["rolle"] = "Recherche"
        if wer == "hinweis": e["name"] = "Hinweis"; e["rolle"] = "Stammtisch"
        self.eintraege.append(e); self.speichern(); return e

    def einwurf(self, text, wer="Roli", anhaenge=None):
        neu = [a for a in (anhang_laden(x) for x in (anhaenge or [])) if a]
        if neu:
            self.anhaenge += neu
            text = (text + " " if text else "") + "(Unterlage mitgebracht: " + ", ".join(a["name"] for a in neu) + ")"
        e = self.eintrag("roli", text, "einwurf"); e["name"] = wer; self.speichern()
        self.einwuerfe.append(f"{wer}: {text}")

    def verlauf_text(self):
        return "\n".join(f"{e['name']} ({e['rolle']}): {e['text']}" for e in self.eintraege[-24:])

    def sprechen(self, wer, auftrag, modell, pruefen=True):
        k = konfig()
        self.letzte_zuege = 1; self.letzte_waechter = []
        system = (seele(wer) + "\n\n## Du sitzt jetzt am KRUG//STAMMTISCH\n"
            f"Thema der Runde: {self.thema}\nGastgeber ist {self.gastgeber} (Masskrugflasche GmbH). Am Tisch: "
            + ", ".join(f"{NAMEN[t]} ({ROLLEN[t]})" for t in self.teilnehmer + list(getattr(self, "fachkraefte", []))) +
            f".\nRegeln: Sprich wie am Tisch, in höchstens {k['max_saetze']} Sätzen und höchstens 60 Wörtern: das Wesentliche zuerst, kein Vorgeplänkel, kein Servus, keine Begrüßung, kein Dank, nichts wiederholen, was schon gesagt wurde. Ganze Sätze, keine Listen, "
            "kein Markdown, keine Überschriften, keine Floskeln. Beziehe dich auf das, was vorher gesagt wurde, "
            "und bring etwas Neues aus deinem Fachgebiet. Sprich nur fuer dich selbst und behaupte nie, was andere am Tisch gesagt haetten, wenn sie noch nicht dran waren. Zahlen und Fakten nur mit Herkunft (Notiz, Quelle) "
            "oder als 'nach meiner Einschätzung'. Jede Tatsache trägt ihre Herkunft in Klammern: (Firmenwissen: Notizname), (Quelle: Adresse), (Tischvorlage) oder die Kennzeichnung als Einschätzung; ohne Herkunft keine Tatsache, ein Fakten-Wächter prüft jeden Beitrag. Nichts erfinden. Steht im Thema eine Marke, ein Produkt oder ein Wort, zu dem du im Firmenwissen "
            "und im Grundwissen nichts findest, dann sag das offen und frag den Gastgeber, statt eine Deutung zu erfinden; der Gastgeber diktiert, "
            "Verhörer sind möglich. Paragrafen, Gesetze und Zahlen nur, wenn du sie sicher kennst.\n\n## Auszüge aus dem Firmenwissen zum Thema\n"
            + (self.wissen or "(keine passenden Notizen gefunden)"))
        if getattr(self, "vorlage", None):
            system += "\n\n## Tischvorlage (vor der Runde geprüft, mit Quellen; gilt als gesichert)\n" + self.vorlage
        else:
            system += "\n\nEs gibt in dieser Runde KEINE Tischvorlage; (Tischvorlage) ist keine gültige Herkunft. Sieh selbst im Firmenwissen oder im Netz nach."
        if self.anhaenge:
            # Unterlagen, die der Gastgeber an den Tisch gelegt hat: jede gekuerzt, damit der Prompt nicht platzt
            system += "\n\n## Unterlagen, die der Gastgeber an den Tisch gelegt hat (lies sie, beziehe dich darauf)\n"
            for a in self.anhaenge[-6:]:
                system += f"\n### {a['name']}\n{a['text'][:9000]}\n"
        nutzer = f"Bisheriges Gespräch:\n{self.verlauf_text() or '(noch nichts)'}\n\n{auftrag}\nAntworte als {NAMEN[wer]}, nur dein Redebeitrag."
        if k.get("modus") == "abo":
            system += ("\n\nDu darfst dafür ausschließlich im Firmenwissen (aktueller Ordner) nachlesen — keine anderen Ordner — und "
                       "bei Bedarf kurz im Netz suchen (dann Quelle nennen). Gib NUR deinen Redebeitrag aus, "
                       "keine Vorbemerkung, keine Werkzeug-Erklärungen.")
            try:
                text, kosten = anfrage_abo(modell, system, nutzer, "high" if modell == k["abo_modell_fazit"] else k.get("abo_aufwand", "medium"))
                self.weg = "abo"
            except Exception as e:
                # Abo an der Grenze oder Störung: Notnagel OpenRouter, damit die Runde nicht abbricht
                self.notiz_fehler = str(e)[:200]
                text, kosten = anfrage(k["modell_runde"] if modell != k["abo_modell_fazit"] else k["modell_fazit"], system, [{"role": "user", "content": nutzer}])
                self.weg = "openrouter (Notnagel)"
        else:
            text, kosten = anfrage(modell, system, [{"role": "user", "content": nutzer}])
            self.weg = "openrouter"
        self.tokens += int(kosten.get("total_tokens", 0) or 0)
        self.letzte_zuege = int(kosten.get("zuege", 1) or 1)
        text = re.sub(r"^\**%s\**(\s*\([^)]*\))?\**\s*[:：]\s*" % NAMEN[wer], "", text).strip()
        text = kuerzen(text, 110 if modell == k["abo_modell_fazit"] else 75)
        if pruefen and k.get("modus") == "abo":
            stellen = herkunft_pruefen(text, bool(getattr(self, "vorlage", ""))) + waechter(text)
            if stellen:
                # Zweiter Versuch: der Sprecher muss belegen, kennzeichnen oder streichen
                nachbesserung = (nutzer + "\n\nWÄCHTER: Diese Stellen deines Beitrags sind unbelegt: " + " | ".join(stellen)
                                 + ". Sieh im Firmenwissen oder im Netz nach und belege sie mit Herkunft, kennzeichne sie als Einschätzung oder streiche sie. Gib den ganzen Beitrag neu aus.")
                try:
                    text2, kosten2 = anfrage_abo(modell, system, nachbesserung, k.get("abo_aufwand", "medium"))
                    self.tokens += int(kosten2.get("total_tokens", 0) or 0)
                    text2 = kuerzen(re.sub(r"^\**%s\**(\s*\([^)]*\))?\**\s*[:：]\s*" % NAMEN[wer], "", text2).strip(), 110 if modell == k["abo_modell_fazit"] else 75)
                    rest = herkunft_pruefen(text2, bool(getattr(self, "vorlage", ""))) + waechter(text2)
                    text = text2
                    self.letzte_waechter = rest
                except Exception:
                    self.letzte_waechter = stellen
            else:
                self.letzte_waechter = []
        return text

    def vorbereiten(self, modell):
        """Tischvorlage: vor der Runde werden Marken, Begriffe und Verhoerer im Thema geklaert, mit Quellen
        (Firmenwissen und Netz). Roli, 10.09.: 'wieso schauen die nicht selber nach im Internet'."""
        system = ("Du bereitest den KRUG//STAMMTISCH vor (Tischvorlage). Aufgabe: 1) Lies das Thema; es ist diktiert, Verhörer sind möglich. "
                  "2) Nenne die Marken, Produkte, Webseiten, Personen und Fachbegriffe darin. 3) Sieh zu jedem im Firmenwissen nach: die Notizenliste unten zeigt alle Dateien, lies die passenden mit Read. "
                  "4) Lies zu jeder genannten Webseite oder Marke die Seite im Netz (WebFetch) und mach eine bis zwei Suchen (WebSearch), auch nach dem Instagram-Auftritt, soweit ohne Login lesbar. "
                  "5) Schreibe die Tischvorlage in Klarschrift, höchstens 220 Wörter, drei Abschnitte: 'Worum es geht' (zwei Sätze), "
                  "'Gesichert' (drei bis sieben Punkte, jeder mit Herkunft in Klammern: Firmenwissen: Notizname oder Quelle: Adresse), "
                  "'Unklar, Rückfrage an den Gastgeber' (null bis drei Fragen, etwa zu Verhörern). Keine Meinung, keine Empfehlung, nichts ohne Herkunft.\n\n"
                  "## Grundwissen\n" + (self.wissen or "") + "\n\n## Alle Notizen im Firmenwissen (zum Nachlesen mit Read, Pfad relativ zum aktuellen Ordner)\n"
                  + "\n".join(sorted(str(q.relative_to(wissen.WURZELN[0])) for q in wissen.WURZELN[0].rglob("*.md"))[:500]))
        try:
            text, kosten = anfrage_abo(modell, system, "Thema der Runde: " + self.thema + "\n\nErstelle jetzt die Tischvorlage.", "medium", max_zuege=16, zeit=420)
        except Exception as e1:
            # Zweiter Versuch, knapper: nur Firmenwissen und eine Netzsuche, damit die Runde nicht ohne Vorlage startet
            try:
                text, kosten = anfrage_abo(modell, system + "\n\nZweiter Versuch: höchstens vier Werkzeug-Aufrufe (Firmenwissen und eine Netzsuche), dann sofort die Vorlage schreiben.",
                                           "Thema der Runde: " + self.thema + "\n\nErstelle jetzt die Tischvorlage.", "low", max_zuege=6, zeit=200)
            except Exception as e2:
                self.vorlage = ""; self.eintrag("vorlage", "Keine Tischvorlage möglich (" + str(e2)[:100] + "). Die Runde läuft ohne geprüfte Fakten; Aussagen sind Einschätzungen.", "vorlage"); return
        self.tokens += int(kosten.get("total_tokens", 0) or 0)
        # Vorrede und Ueberschrift weg: die Vorlage beginnt bei "Worum es geht"
        t = text.strip(); m = re.search(r"(\*\*|#+\s*)?Worum es geht", t)
        if m: t = t[m.start():]
        self.vorlage = re.sub(r"^#+ .*\n", "", t)[:2200]
        self.eintrag("vorlage", self.vorlage, "vorlage")

    def kollegen_holen(self, modell):
        """Sepp waehlt zwei bis vier Leiter fuer das Thema aus und setzt sie an den Tisch."""
        import json as _j
        wahl = ", ".join(f"{k} = {NAMEN[k]} ({ROLLEN[k]})" for k in NAMEN if k != "sepp")
        auftrag = (f"Thema der Runde: {self.thema}\n\nWaehle aus diesen Kollegen zwei bis vier, die fuer das Thema gebraucht werden: {wahl}. "
                   "Antworte NUR mit JSON: {\"kollegen\": [\"kurzname\", ...], \"begruendung\": \"ein Satz\"}")
        try:
            text, kosten = anfrage_abo(modell, seele("sepp") + "\n\nDu bist der Koordinator und stellst das Team zusammen. Keine Rede, nur JSON.", auftrag) if konfig().get("modus") == "abo" else anfrage(modell, seele("sepp"), [{"role": "user", "content": auftrag}])
            self.tokens += int((kosten or {}).get("total_tokens", 0) or 0)
            m = re.search(r"\{.*\}", text, re.S); d = _j.loads(m.group(0)) if m else {}
            neu = [x for x in d.get("kollegen", []) if x in NAMEN and x != "sepp"][:4]
        except Exception as e:
            neu, d = [], {"begruendung": f"Auswahl fehlgeschlagen ({str(e)[:60]})"}
        if not neu: neu = ["timo", "greta"]
        self.teilnehmer = ["sepp"] + neu; self.speichern()
        self.eintrag("sepp", "Zu dem Thema hole ich " + ", ".join(NAMEN[x] + " (" + ROLLEN[x] + ")" for x in neu) + " an den Tisch. " + str(d.get("begruendung", "")).strip(), "rede")

    def fachkraefte_holen(self, modell):
        """Sepp sieht ins Personalverzeichnis und holt null bis zwei Fachkraefte auf Zeit an den Tisch
        (Roli, 10.09.: 'von denen kriegen wir Informationen mit kleinem Beitrag')."""
        import json as _j
        liste = fachkraefte_liste()
        if not liste: return
        katalog = "\n".join(f"{k}: {v[0]} ({v[2]}). {v[1]}" for k, v in liste.items())
        auftrag = (f"Thema der Runde: {self.thema}\n\nPersonalverzeichnis der Fachkraefte:\n{katalog}\n\n"
                   "Waehle null bis zwei Fachkraefte, deren Fachwissen fuer dieses Thema einen eigenen Beitrag bringt, den die Abteilungsleiter nicht haben. "
                   "Antworte NUR mit JSON: {\"fachkraefte\": [\"kennung\", ...], \"begruendung\": \"ein Satz\"}")
        try:
            text, kosten = anfrage_abo(modell, seele("sepp") + "\n\nDu bist der Koordinator und stellst das Team zusammen. Keine Rede, nur JSON.", auftrag, "low")
            self.tokens += int((kosten or {}).get("total_tokens", 0) or 0)
            m = re.search(r"\{.*\}", text, re.S); d = _j.loads(m.group(0)) if m else {}
            neu = [fachkraft_anmelden(x) for x in d.get("fachkraefte", []) if x in liste][:2]
        except Exception as e:
            neu, d = [], {}
        self.fachkraefte = [x for x in neu if x]; self.speichern()
        for x in self.fachkraefte:
            threading.Thread(target=fachkraft_portraet, args=(x[3:], NAMEN[x], ROLLEN[x]), daemon=True).start()
        if self.fachkraefte:
            self.eintrag("sepp", "Dazu hole ich als Fachkraft auf Zeit " + " und ".join(NAMEN[x] + " (" + ROLLEN[x] + ")" for x in self.fachkraefte) + " an den Tisch. " + str(d.get("begruendung", "")).strip(), "rede")

    def laufen(self):
        k = konfig()
        if k.get("modus") == "abo":
            k = dict(k, modell_runde=k["abo_modell_runde"], modell_fazit=k["abo_modell_fazit"])
        try:
            self.aktuell = "sepp"
            if self.teilnehmer == ["sepp"]:
                # Nur Sepp am Tisch: er holt sich selbst die passenden Leiter (Aufstellung 09.09.),
                # statt so zu tun, als saessen die anderen schon da.
                self.kollegen_holen(k["modell_runde"])
            if k.get("modus") == "abo":
                self.vorbereiten(k["modell_runde"])
            if k.get("modus") == "abo":
                self.fachkraefte_holen(k["modell_runde"])
            self.eintrag("sepp", self.sprechen("sepp", "Eröffne die Runde in zwei Sätzen: Thema als Frage, dann das Wort weitergeben. Keine Begrüßung. Nennt die Tischvorlage offene Rückfragen, stell sie dem Gastgeber zuerst; die Runde läuft trotzdem weiter. Sprich nur für dich; die anderen antworten gleich selbst.", k["modell_runde"]))
            for nr in range(self.runden):
                for wer in [t for t in self.teilnehmer if t != "sepp"] + list(self.fachkraefte) + (["sepp"] if nr < self.runden - 1 else []):
                    while self.pause and not self.stop: time.sleep(0.4)
                    if self.stop: break
                    self.aktuell = wer
                    auftrag = f"Runde {nr+1} von {self.runden}."
                    if self.einwuerfe:
                        auftrag += " WICHTIG: Roli hat eingeworfen: '" + " | ".join(self.einwuerfe) + "'. Geh zuerst darauf ein."
                        self.einwuerfe = []
                    if wer == "sepp":
                        auftrag += " Als Koordinator: Fasse den Zwischenstand in zwei Sätzen zusammen und stelle die nächste Frage."
                    if wer.startswith("fk:"):
                        auftrag += " Du bist Fachkraft auf Zeit: bring in höchstens drei Sätzen den einen Punkt aus deinem Fachgebiet, der dem Gastgeber jetzt weiterhilft, mit Herkunft."
                    self.eintrag(wer, self.sprechen(wer, auftrag, k["modell_runde"]))
                if self.stop: break
            while self.pause and not self.stop: time.sleep(0.4)
            self.aktuell = "sepp"
            fazit = "Schließe die Runde: Fasse die Ergebnisse zusammen, nenne die zwei bis drei wichtigsten Empfehlungen und die Entscheidungen, die bei Roli liegen. Höchstens 5 Sätze, höchstens 90 Wörter."
            if self.einwuerfe:
                fazit += " Berücksichtige Rolis Einwürfe: " + " | ".join(self.einwuerfe); self.einwuerfe = []
            self.eintrag("sepp", self.sprechen("sepp", fazit, k["modell_fazit"]), "fazit")
            self.status = "fertig"; self.aktuell = None; self.speichern()
            from . import ausgabe
            self.pdf = ausgabe.pdf_und_notiz(self); self.speichern()
        except Exception as e:
            self.status = "fehler"; self.fehler = str(e)[:300]; self.aktuell = None; self.speichern()

    @classmethod
    def aus_datei(cls, rid):
        """Fertige Runde aus der Ablage wiederherstellen, damit Roli nachfragen kann."""
        p = RUNDEN / f"{rid}.json"
        if not re.fullmatch(r"[0-9-]+", rid or "") or not p.exists(): return None
        d = json.loads(p.read_text())
        r = cls.__new__(cls)
        r.id = d["id"]; r.thema = d["thema"]; r.gastgeber = d.get("gastgeber", "Roli")
        r.teilnehmer = d["teilnehmer"]; r.runden = d.get("runden", 2); r.eintraege = d.get("eintraege", [])
        r.status = d["status"]; r.einwuerfe = []; r.pause = False; r.stop = False; r.aktuell = None
        r.tokens = d.get("tokens", 0); r.pdf = d.get("pdf"); r.fehler = None; r.weg = d.get("weg"); r.notiz_fehler = None
        r.wissen = wissen.auszug(r.thema); r.anhaenge = []
        r.vorlage = next((e["text"] for e in r.eintraege if e.get("art") == "vorlage"), "")
        r.fachkraefte = [fachkraft_anmelden(x["kurz"][3:]) for x in d.get("fachkraefte", [])]; r.fachkraefte = [x for x in r.fachkraefte if x]
        return r

    def fortsetzen(self, text, wer="Roli"):
        """Nachfrage des Gastgebers zu einer fertigen Runde: Einwurf, eine weitere Runde, neues Fazit."""
        k = konfig()
        if k.get("modus") == "abo":
            k = dict(k, modell_runde=k["abo_modell_runde"], modell_fazit=k["abo_modell_fazit"])
        self.status = "läuft"; self.einwurf(text, wer)
        try:
            for w in [t for t in self.teilnehmer if t != "sepp"] + list(getattr(self, "fachkraefte", [])):
                while self.pause and not self.stop: time.sleep(0.4)
                if self.stop: break
                self.aktuell = w
                auftrag = f"Nachfrage-Runde. WICHTIG: {wer} hat nachgefragt: '{text}'. Antworte genau darauf aus deinem Fachgebiet."
                if self.einwuerfe:
                    auftrag += " Weitere Einwürfe: " + " | ".join(self.einwuerfe); self.einwuerfe = []
                self.eintrag(w, self.sprechen(w, auftrag, k["modell_runde"]))
            self.aktuell = "sepp"
            self.eintrag("sepp", self.sprechen("sepp", f"Schließe die Nachfrage-Runde zu '{text}': Was ist die Antwort für {wer} in höchstens 4 Sätzen, und was liegt bei ihm zur Entscheidung?", k["modell_fazit"]), "fazit")
            self.status = "fertig"; self.aktuell = None; self.speichern()
            from . import ausgabe
            self.pdf = ausgabe.pdf_und_notiz(self); self.speichern()
        except Exception as e:
            self.status = "fehler"; self.fehler = str(e)[:300]; self.aktuell = None; self.speichern()

    def weiterfuehren(self):
        """Nach einem Neustart des Dienstes: unterbrochene Runde zu Ende bringen (Roli, 10.09. 22:51: 'ist der
        Stammtisch defekt?'). Alle sprechen noch einmal mit Bezug auf das Bisherige, dann schliesst Sepp."""
        k = konfig()
        if k.get("modus") == "abo":
            k = dict(k, modell_runde=k["abo_modell_runde"], modell_fazit=k["abo_modell_fazit"])
        self.status = "läuft"; self.eintrag("hinweis", "Der Stammtisch-Dienst wurde neu gestartet; die Runde wird fortgesetzt.", "hinweis")
        try:
            for w in [t for t in self.teilnehmer if t != "sepp"] + list(getattr(self, "fachkraefte", [])):
                while self.pause and not self.stop: time.sleep(0.4)
                if self.stop: break
                self.aktuell = w
                self.eintrag(w, self.sprechen(w, "Die Runde wurde kurz unterbrochen und geht weiter. Setze das Gespräch fort: greif den letzten Stand auf und bring deinen nächsten Punkt.", k["modell_runde"]))
            self.aktuell = "sepp"
            self.eintrag("sepp", self.sprechen("sepp", "Schließe die Runde: Fasse die Ergebnisse zusammen, nenne die zwei bis drei wichtigsten Empfehlungen und die Entscheidungen, die bei Roli liegen. Höchstens 5 Sätze, höchstens 90 Wörter.", k["modell_fazit"]), "fazit")
            self.status = "fertig"; self.aktuell = None; self.speichern()
            from . import ausgabe
            self.pdf = ausgabe.pdf_und_notiz(self); self.speichern()
        except Exception as e:
            self.status = "fehler"; self.fehler = str(e)[:300]; self.aktuell = None; self.speichern()

AKTIV = {}
def wiederaufnehmen():
    """Beim Start des Dienstes: Runden, die laut Datei noch laufen, aber keinen Faden mehr haben, fortsetzen."""
    n = 0
    for p in sorted(RUNDEN.glob("*.json")):
        try: d = json.loads(p.read_text())
        except Exception: continue
        if d.get("status") in ("läuft", "pause") and d["id"] not in AKTIV:
            r = Runde.aus_datei(d["id"])
            if not r: continue
            AKTIV[r.id] = r; threading.Thread(target=r.weiterfuehren, daemon=True).start(); n += 1
    return n

def nachfragen(rid, text, wer="Roli"):
    r = AKTIV.get(rid) or Runde.aus_datei(rid)
    if not r: return None
    if r.status in ("läuft", "pause"): raise RuntimeError("Diese Runde läuft noch, nutze den Einwurf.")
    AKTIV[r.id] = r
    threading.Thread(target=r.fortsetzen, args=(text, wer), daemon=True).start()
    return r

def loeschen(rid):
    """Runde samt PDF aus der Bibliothek entfernen (Roli, 10.09.). Laufende Runden bleiben."""
    r = AKTIV.get(rid)
    if r and r.status in ("läuft", "pause"): raise RuntimeError("Diese Runde läuft noch.")
    p = RUNDEN / f"{rid}.json"
    if not re.fullmatch(r"[0-9-]+", rid or "") or not p.exists(): return False
    try:
        d = json.loads(p.read_text())
        if d.get("pdf"):
            pdf = DATEN.parent / "Downloads" / "Stammtisch" / d["pdf"]
            if pdf.exists() and "/" not in d["pdf"]: pdf.unlink()
        # Roli, 10.09.: geloescht heisst auch aus dem Firmenwissen raus (Protokoll-Notiz und HTML), sonst liest der
        # naechste Stammtisch alte, womoeglich erfundene Aussagen als Wissen
        from . import ausgabe
        rr = Runde.aus_datei(rid)
        if rr:
            name = ausgabe.dateiname(rr)
            for q in (pathlib.Path("/home/BENUTZER/Notizen/06 Firmenwissen/12 Stammtisch") / f"{name}.md", ausgabe.AUSGABE / f"{name}.html"):
                if q.exists(): q.unlink()
    except Exception: pass
    p.unlink(); AKTIV.pop(rid, None); return True

def starten(thema, teilnehmer, runden=None, gastgeber="Roli", anhaenge=None):
    r = Runde(thema, teilnehmer, runden, gastgeber, anhaenge)
    AKTIV[r.id] = r
    threading.Thread(target=r.laufen, daemon=True).start()
    return r

def laden(rid):
    if rid in AKTIV: return AKTIV[rid].zustand()
    p = RUNDEN / f"{rid}.json"
    if not p.exists(): return None
    d = json.loads(p.read_text())
    # Portraets koennen nach dem Rundenende fertig geworden sein: beim Lesen nachsehen
    for f in d.get("fachkraefte", []):
        fid = f.get("kurz", "")[3:]
        if fid and f.get("bild", "").endswith("gast.png") and ((PORTRAETS / f"{fid}.png").exists() or runden_und_ablegen(fid)):
            f["bild"] = f"stammtisch/fk/{fid}.png"
    return d

def alle(fuer=None):
    """Bibliothek. `fuer` = Name des Gastgebers: dann nur dessen eigene Runden (Roli sieht alle,
    Beschluss 12.09.2026: Gischi und Denis arbeiten am selben Tisch, sehen aber nur ihr eigenes)."""
    liste = []
    for p in sorted(RUNDEN.glob("*.json"), reverse=True):
        try:
            d = json.loads(p.read_text())
            if fuer and fuer != "Roli" and (d.get("gastgeber") or "Roli") != fuer: continue
            liste.append({"id": d["id"], "thema": d["thema"], "status": d["status"], "pdf": d.get("pdf"),
                          "eintraege": len(d.get("eintraege", [])), "datum": d["id"][:8], "gastgeber": d.get("gastgeber", "Roli")})
        except Exception: continue
    return liste
