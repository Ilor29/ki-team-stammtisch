# Bauplan — so baut man einen Stammtisch nach

Stand: 12.09.2026 (Fakten-Sicherung, Fachkraefte, Umzug). Das Baubuch (`BAUBUCH.md`) erzählt, was beim Bauen passiert ist. Dieser
Bauplan sagt, wie man den Stammtisch von Null neu baut, für Krugmeister oder für eine andere
Firma. Wer ihn liest, soll ihn ohne Nachfragen umsetzen können.

## Was der Stammtisch ist

Ein Besprechungsraum im Browser. Der Gastgeber gibt ein Thema vor, wählt Kollegen aus dem
KI-Team, und die Kollegen besprechen das Thema reihum, sichtbar auf einer Bühne mit Bild und
Sprechblase. Der Gastgeber kann dazwischenreden, Unterlagen an den Tisch legen, die Glocke
läuten (Pause) oder die Runde beenden. Am Ende fasst der Koordinator zusammen, und aus dem
Gespräch werden ein PDF und eine Notiz im Zweitgehirn. Alle Runden bleiben in einer
Bibliothek.

Was er nicht ist: kein Chat mit einer KI und kein Rechercheteam. Die Kollegen reden auf
Basis des Firmenwissens und dürfen höchstens kurz im Netz nachschlagen. Echte Rechercheaufträge
laufen über das Hermes-Team und seine Tafel.

## Die fünf Teile

1. **Der Motor** (`stammtisch/motor.py`). Eine Klasse `Runde` hält Thema, Teilnehmer,
   Rundenzahl, Einträge, Status (läuft, pause, fertig, fehler), offene Einwürfe, mitgebrachte
   Unterlagen, Gastgeber. Der Ablauf läuft in einem Hintergrund-Thread: der Koordinator
   eröffnet, dann spricht in jeder Runde jeder einmal, zwischen den Runden fasst der
   Koordinator zusammen, am Ende folgt sein Fazit. Jeder Redebeitrag ist genau ein
   Modellaufruf. Der System-Prompt besteht aus der Seele der Person, den Tischregeln (höchstens
   sechs Sätze, keine Listen, kein Markdown, Fakten nur mit Herkunft, nichts erfinden), den
   Auszügen aus dem Firmenwissen und den Unterlagen. Der Nutzer-Prompt enthält den bisherigen
   Verlauf (die letzten 24 Beiträge) und den Auftrag für diesen Beitrag. Einwürfe des
   Gastgebers bekommt der nächste Sprecher vorangestellt, mit der Anweisung, zuerst darauf
   einzugehen. Jede Änderung wird sofort als JSON gespeichert
   (`~/stammtisch-daten/runden/<id>.json`), damit die Oberfläche nur abfragen muss.

2. **Das Wissen** (`stammtisch/wissen.py`). Vor der Runde sucht der Motor Notizen, die zum
   Thema passen: einfache Wortüberschneidung zwischen Thema und Notiztext, die besten sechs
   als Auszüge mit je 1.400 Zeichen. Dazu kommen immer drei Grundwissen-Notizen (Firma, Produkt,
   Sortiment), weil eine Person sonst Dinge für neu hält, die es längst gibt. Gesucht wird nur
   im Ordner `06 Firmenwissen` des Zweitgehirns, nie in privaten Notizen.

3. **Die Ausgabe** (`stammtisch/ausgabe.py`). Nach dem Fazit entsteht ein Markdown-Protokoll
   mit Frontmatter (titel, typ protokoll, tags, stand), das über `~/.notizen-schreiben.py` in
   den Ordner `06 Firmenwissen/12 Stammtisch` des Zweitgehirns geht, ein PDF im FELD//PULS-Stil
   über den kopflosen Chromium des Browser-Prüfers nach `~/Downloads/Stammtisch/`, und eine
   Zeile im gemeinsamen Ereignis-Log (`~/.ereignis.sh`).

4. **Der Dienst** (`stammtisch/server.py`). FastAPI auf 127.0.0.1, Port 8806, gestartet von
   systemd (`deploy/stammtisch.service`, Restart always). Schnittstelle: Runde starten (nur
   eine gleichzeitig, sonst 409), Stand abfragen, Einwurf, Glocke, Stopp, Liste aller Runden,
   PDF ausliefern, Diktat glätten, Unterlage hochladen. Der angemeldete Name kommt von Caddy im
   Kopf `X-Nutzer` und wird zum Gastgeber-Namen.

5. **Die Oberfläche** (`web/index.html`, eine Datei ohne Framework). Bühne mit Saalbild und
   Sitzplätzen in Prozentkoordinaten, Sprechblase, die den Beitrag tippend abspielt, Glow beim
   Sprecher, Puls beim nächsten. Start-Formular mit Thema, Teilnehmern, Rundenzahl. Die
   Oberfläche fragt alle 1,5 Sekunden den Stand ab und spielt neue Beiträge nacheinander ab.
   Darunter Protokoll, PDF-Knopf, Teilen (Web-Share mit der PDF-Datei aufs Handy) und die
   Bibliothek. Die beiden Textfelder (Thema, Einwurf) folgen dem Relay-Aufbau, siehe unten.

## Die Personen

Jede Person hat eine Seele, das ist eine Markdown-Datei mit Name, Aufgabe, Haltung,
Sprechweise und den Fakten-Regeln (Zahlen nur mit Herkunft, Rechts- und Steuerthemen sind
Einschätzungen, keine Beratung). Die Seelen werden nicht kopiert, sondern live aus den
Hermes-Profilen gelesen (`~/.hermes/profiles/<profil>/SOUL.md`), damit es nur eine Wahrheit
gibt. Anweisungen, die nur für die Kanban-Tafel gelten, filtert der Motor heraus. Ein
Koordinator ist Pflicht (bei Krugmeister Sepp): er eröffnet, moderiert und schließt. Die
übrigen Personen decken je ein Fachgebiet ab (bei Krugmeister Werberecht, Finanzen, Marketing,
Export, Logistik). Bilder: eine freigestellte Figur pro Person in `web/stammtisch/`.

## Die Fakten-Sicherung (Beschluss 10.09.2026, nach einer Falschauskunft)

Der wichtigste Teil, ohne den der Stammtisch gefaehrlich ist: Ein schluessig klingendes Fazit auf
erfundener Grundlage ist schlimmer als eine Luecke. Fuenf Sicherungen, alle im Abo-Weg:

1. **Steckbrief aller Haeuser** als Grundwissen in jeder Runde (bei Roland
   `06 Firmenwissen/10 Strategie/Rolis Haeuser und Marken.md`, 2.600 Zeichen). Ohne ihn deutet das
   Team unbekannte Marken frei (Anlassfall: Alkohol-Werberecht auf ein KI-Skill-Verzeichnis angewandt).
2. **Tischvorlage** vor der Eroeffnung (`Runde.vorbereiten`): ein eigener Aufruf liest das Thema, sucht
   im Netz, liest die genannten Webseiten, sieht im Firmenwissen nach (Liste aller Notizen wird
   mitgegeben, weil Grep und Glob gesperrt sind) und schreibt drei Abschnitte: „Worum es geht",
   „Gesichert" mit Herkunft je Punkt, „Unklar, Rueckfrage an den Gastgeber". Bis 16 Zuege, 7 Minuten,
   ein knapper zweiter Versuch bei Fehlschlag. Erscheint als eigener Eintrag (`art=vorlage`).
3. **Herkunftspflicht** je Tatsache: `(Firmenwissen: Notiz)`, `(Quelle: Adresse)`, `(Tischvorlage)`
   oder als Einschaetzung gekennzeichnet. Gibt es keine Vorlage, ist `(Tischvorlage)` ungueltig.
4. **Fakten-Waechter** (`waechter`, Haiku ohne Werkzeuge, JSON-Schema) plus feste Pruefung
   (`herkunft_pruefen`: zitierte Notiz muss existieren). Bei Befund muss der Sprecher denselben
   Beitrag neu liefern, belegt, gekennzeichnet oder gestrichen; bleibt etwas offen, steht es sichtbar
   unter dem Beitrag (Feld `waechter`). Ein Nachsehen im Netz oder Wissen wird als `nachgesehen`
   vermerkt.
5. **Rueckfrage statt Deutung:** Bei unbekannter Marke oder unklarem Wort fragt der Koordinator den
   Gastgeber zuerst; die Runde laeuft trotzdem weiter. Der Gastgeber diktiert, Verhoerer sind normal.

Werkzeuge der Personen sind bewusst eng: Websuche, Webseite lesen, Lesen NUR im Firmenwissen. Grep und
Glob sind entfernt, weil sie sich nicht auf einen Ordner begrenzen lassen (geprueft 10.09.: Grep las
das Gedaechtnis trotz Verbotsregel). Das ist auch der Schutz fuer den zweiten Gastgeber.

## Die Fachkraefte auf Zeit (Beschluss 10.09.2026)

Neben den Abteilungsleitern gibt es 82 Fachrollen (aus agency-agents, Auswahl Roland), je eine Datei in
`~/.hermes/fachkraefte/<kennung>.md`, mit einem Satz je Rolle im Personalverzeichnis
(`~/projekte/agenten-liste/PERSONALVERZEICHNIS.md`). Ablauf: Der Koordinator liest vor der Eroeffnung
das Verzeichnis und holt null bis zwei Fachkraefte (`fachkraefte_holen`), sagt als Beitrag wen und
warum. Sie sprechen je Runde einmal, drei Saetze, ihren einen Fachpunkt mit Herkunft. Kuerzel `fk:<id>`,
Seele ist die Rollen-Datei mit Stammtisch-Rahmen (Deutsch, kein Fachjargon, nur ihr Gebiet).
Gesicht: Beim ersten Einsatz erzeugt `fachkraft_portraet` ein rundes Portraet im Stil der Leiter
(nano-banana-2-lite, 4 Credits, Aussehen stabil aus der Kennung abgeleitet), Ablage
`web/stammtisch/fk/<id>.png`. Das laeuft in einem eigenen Faden, damit die Runde nicht wartet, und wird
nachtraeglich uebernommen, auch in fertigen Runden. Buehne: vier Gast-Plaetze am Tisch.

## Bedienung durch den Gastgeber (Stand 10.09.2026)

- **Tempo der Sprechblasen:** Knopf im Kopf, drei Stufen (gemuetlich 45 ms je Zeichen und lange
  Haltezeit, normal, flott), Wahl bleibt im Browser. Tippen auf die Blase zeigt den Rest sofort.
  Grund: Roland liest live mit und kam nicht hinterher.
- **Laenge:** hoechstens 3 Saetze und 60 Woerter je Beitrag, Fazit 5 Saetze; kein Servus, kein Dank.
  Der Motor kuerzt zusaetzlich auf ganze Saetze (`kuerzen`, 75 bzw. 110 Woerter).
- **Nachfragen nach dem Ende:** Die Leiste bleibt stehen („Nachfrage an den Tisch"),
  `POST /api/runde/<id>/nachfrage` stellt die Runde aus der Datei wieder her (`Runde.aus_datei`), alle
  antworten einmal auf die Nachfrage, der Koordinator schliesst neu, PDF und Notiz werden erneuert.
- **Bibliothek mit Papierkorb:** `DELETE /api/runde/<id>` loescht JSON, PDF, HTML und die
  Protokoll-Notiz im Firmenwissen. Laufende Runden nie. Lösch-Tests nur an Kopien mit Probe-Kennung.
- **Neustart:** `wiederaufnehmen()` beim Start des Dienstes findet Runden im Status laeuft oder pause
  ohne Faden und fuehrt sie zu Ende (Hinweis-Eintrag, alle sprechen noch einmal, Fazit). Trotzdem gilt:
  vor einem Neustart auf laufende Runden pruefen.

## Die Modelle und die Kosten

Standard ist der Abo-Weg: jeder Beitrag ist ein Aufruf von `claude -p` über das Claude-Abo,
mit den Werkzeugen Websuche, Webseite lesen und Lesen nur im Ordner Firmenwissen (Read-Regel
in `--allowedTools`, Arbeitsordner ist der Wissensordner). Runden laufen auf Sonnet, das Fazit
auf Opus. Das kostet nichts extra, dauert aber 20 bis 40 Sekunden je Beitrag. Der Notnagel ist
OpenRouter (Haiku für Runden, Sonnet fürs Fazit, Schlüssel in `~/.stammtisch-schluessel`,
Rechte 600), wenn das Abo an der Grenze ist. Umschalten in `~/stammtisch-daten/config.json`
mit dem Feld `modus`. Das Feld `weg` im Runden-Zustand zeigt, welcher Weg gelaufen ist.

## Die Eingabefelder (Beschluss vom 05.09.2026)

Jedes Textfeld mit Mikrofon sieht aus wie das Relay-Eingabefeld, nicht anders: abgerundeter
Rahmen, oben das Textfeld, das beim Diktieren mitwächst, darunter Plus, Mikrofon, zwei Funken
zum Glätten, beim Zuhören ein rotes Verwerfen-Kreuz, rechts der runde orange Senden-Pfeil.
Das Plus öffnet ein Blatt von unten mit Kamera, Fotos und Dateien. Das Diktat läuft satzweise
(nicht durchgehend, Android-Chrome hängt sonst), das Glätten über `claude -p` mit Haiku und
einer Kostenbremse, Entwürfe bleiben im localStorage. Unterlagen kommen roh in den Body von
`/api/anhang`, der Name im Kopf `X-Dateiname`; PDF liest pdftotext, Word und Co. kommen aus dem
XML, Fotos liest das Abo-Modell mit dem Read-Werkzeug vor. Die Texte (höchstens 60.000
Zeichen je Datei, je Beitrag die letzten sechs mit je 9.000 Zeichen) gehen als eigener
Abschnitt in den System-Prompt. Die genaue Bauanleitung mit Referenzbildern steht im
Koffer-Skill `diktat-im-browser`.

## Zugang und Schutz

Caddy vor dem Dienst mit basicauth, ein Benutzer je Gastgeber, und `header_up X-Nutzer
{http.auth.user.id}`, dazu `frame-ancestors` für das Cockpit, noindex, kein Server-Header.
Passwörter nur in `~/.stammtisch-zugaenge.txt` (nicht in Git). Ein zweiter Gastgeber (bei
Krugmeister die Vertriebspartnerin) bekommt einen eigenen Benutzer; damit er nichts Privates sieht, lesen die
Personen nur den Ordner Firmenwissen, und die Prompts sprechen von der Geschäftsführung statt
von einer Person. Der Dienst hängt an der Dienst-Wache und im LEIT//PULS als eigener Reiter.

## Die Reihenfolge beim Bauen

1. Projektordner mit `.venv` (fastapi, uvicorn, markdown), Datenordner `~/stammtisch-daten`
   mit `runden` und `anhaenge`.
2. Personen festlegen: Koordinator plus vier bis sechs Fachleute, Seelen als Hermes-Profile,
   je ein Bild.
3. Motor schreiben und mit zwei Personen und einer Runde über die Schnittstelle testen,
   noch ohne Oberfläche. Prüfen, ob die Person das Grundwissen kennt.
4. Wissen anschließen (Ordner, Grundwissen-Notizen), Ausgabe anschließen (Notiz, PDF,
   Ereignis).
5. Oberfläche bauen: erst das Mockup auf dem eigenen Server zeigen (`leitstand/mockups`),
   erst nach dem Ja die Bühne bauen. Eingabefelder im Relay-Aufbau.
6. Dienst, Caddy, Dienst-Wache, Reiter im Cockpit, Zugänge.
7. Eine echte Runde mit dem Gastgeber, danach Baubuch und Register nachtragen.

## Auf einen zweiten Server bringen (Frage Roland, 12.09.2026)

Der Stammtisch selbst ist klein: Python-Dienst, eine HTML-Datei, Bilder, Datenordner. Umzugsaufwand
liegt nicht im Programm, sondern an drei Abhaengigkeiten. Reihenfolge und Entscheidungen:

1. **Programm und Bilder:** Repo klonen, `.venv` mit fastapi, uvicorn, markdown, Pillow; Datenordner
   `~/stammtisch-daten` mit `runden` und `anhaenge`; systemd-Dienst auf 127.0.0.1:8806, Caddy davor mit
   basicauth je Gastgeber und `header_up X-Nutzer`. Ein halber Tag.
2. **Das Abo (die eigentliche Huerde):** Jeder Beitrag ist ein `claude -p`-Aufruf. Auf dem zweiten
   Server muss Claude Code installiert und mit demselben Konto angemeldet sein; das kann nur der
   Mensch tun (`claude login` im Terminal dort, oder ein Jahres-Token). Ohne das laeuft nur der
   OpenRouter-Notnagel, der kostet Guthaben und ist schwaecher.
3. **Das Wissen:** Die Personen lesen den Ordner Firmenwissen. Entweder eine Kopie dorthin spiegeln
   (dann veraltet sie und Aenderungen laufen auseinander) oder den Ordner ueber das Netz einhaengen.
   Empfehlung: der Server, auf dem der Stammtisch laeuft, muss den aktuellen Wissensordner haben,
   sonst ist die Fakten-Sicherung wertlos.
4. **Die Seelen:** kommen live aus `~/.hermes/profiles/*/SOUL.md` plus `~/.hermes/fachkraefte/`. Beide
   Ordner mitspiegeln (nur Lesen), Portraets liegen im Repo.

**Empfehlung statt Umzug:** Nicht zwei Stammtische betreiben. Zwei Instanzen heissen zwei Bibliotheken,
zwei Notiz-Baeume und zwei Wahrheiten, und der zweite Gastgeber sieht die Runden des ersten nicht. Der
Stammtisch gehoert dorthin, wo Wissen und Abo liegen; ein zweiter Gastgeber bekommt einen eigenen
Caddy-Benutzer und dieselbe Adresse. Soll der Stammtisch trotzdem auf dem Krugmeister-Server laufen,
dann als **Umzug, nicht als Zweitstueck**: Wissensordner und Hermes-Ordner dorthin spiegeln, Abo dort
anmelden, Datenordner mitnehmen, alte Adresse auf die neue umleiten, und dann den Dienst hier abschalten.

## Was man für eine andere Firma ändert

Die Personen und ihre Seelen, das Saalbild und die Sitzplätze, den Wissensordner und die drei
Grundwissen-Notizen, den Firmennamen in den Prompts, die Zugänge in Caddy und das Farbschema
der Oberfläche. Motor, Wissen, Ausgabe, Dienst und Eingabefelder bleiben gleich. Das ist der
Kern des Produkts „KI-Kontor" (siehe Notiz `02 Projekte/KI-Kontor als Produkt`).

## Stolperfallen, schon bezahlt

- `hidden` verliert gegen `display:flex` in der CSS-Regel; deshalb `[hidden]{display:none
  !important}` an den Anfang.
- Das Mikrofon nie mit `continuous = true` betreiben, Android-Chrome hängt jeden Zwischenstand
  neu an.
- Keine deutschen Anführungszeichen in Python-Strings, wenn man den Code per Heredoc schreibt.
- Web-Share mit Datei geht nur über HTTPS und am Handy; am Rechner öffnet sich das PDF.
- Der Gastgeber-Name muss bis in `starten()` durchgereicht werden, sonst stürzt die Runde des
  zweiten Gastgebers ab.
- Bildmodelle schreiben Text unzuverlaessig (Umlaute werden zu OE): Bild ohne Text erzeugen und den
  Text mit `Medienwerk/werkzeuge/textsetzer.py` und echter Schrift daraufsetzen.
- Ein Dienst-Neustart mitten in einer Runde reisst den Gespraechsfaden ab; der Faden lebt im Speicher.
- Wer einen Entwurf „nach Beschluss" umbaut, öffnet vorher das Archiv und fragt, welches Teil
  gemeint ist. Nicht die ganze Bühne umbauen, wenn nur das Mikrofon gemeint war.
