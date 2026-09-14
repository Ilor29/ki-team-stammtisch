"""Wissens-Auszug fürs Gespräch: sucht in Rolis Zweitgehirn die Notizen, die zum Thema
passen, und liefert kurze Auszüge. Bewusst simpel (Wortüberschneidung), das reicht für
ein paar hundert Notizen und braucht keinen Vektor-Dienst."""
import re, pathlib

WURZELN = [pathlib.Path("/home/BENUTZER/Notizen/06 Firmenwissen")]  # nur Firmenwissen: der Stammtisch ist auch fuer die Vertriebspartnerin da
STOPP = set("und oder der die das den dem des ein eine einer eines für mit von zu im in an auf ist sind wir uns unser unsere unseren wie was wo welche welcher welches soll sollen kann können mehr noch auch nicht bei nach aus über als um es sich zum zur".split())

def woerter(text):
    return [w for w in re.findall(r"[a-zäöüß0-9]{3,}", text.lower()) if w not in STOPP]

def auszug(thema, max_notizen=6, max_zeichen=1400):
    suchw = set(woerter(thema))
    if not suchw:
        return ""
    treffer = []
    for wurzel in WURZELN:
        for p in wurzel.rglob("*.md"):
            try:
                t = p.read_text(errors="replace")
            except OSError:
                continue
            tw = t.lower()
            punkte = sum(tw.count(w) for w in suchw) + 5 * sum(1 for w in suchw if w in p.stem.lower())
            if punkte > 0:
                treffer.append((punkte, p, t))
    treffer.sort(key=lambda x: -x[0])
    teile = []
    # Grundwissen zur Firma immer dabei, damit niemand "neu für uns" sagt, was es längst gibt
    for g in ["06 Firmenwissen/10 Strategie/Rolis Haeuser und Marken.md", "06 Firmenwissen/04 Produkte/Krugmeister.md", "06 Firmenwissen/04 Produkte/Maßkrugflasche.md",
              "06 Firmenwissen/04 Produkte/Krugmeister Weitere Sorten und Merchandise.md"]:
        gp = pathlib.Path("/home/BENUTZER/Notizen") / g
        if gp.exists():
            gt = re.sub(r"^---\n.*?\n---\n", "", gp.read_text(errors="replace"), flags=re.S).strip()
            teile.append(f"### {gp.stem} (Grundwissen)\n{gt[:2600 if 'Haeuser' in gp.stem else 900]}")
    for punkte, p, t in treffer[:max_notizen]:
        if any(p.stem in x for x in teile): continue
        t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S).strip()
        teile.append(f"### {p.stem}\n{t[:max_zeichen]}")
    return "\n\n".join(teile)
