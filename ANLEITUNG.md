# Anleitung: vom leeren Server zur ersten Stammtisch-Runde

Diese Anleitung führt in neun Schritten durch den Aufbau. Wer den Bauplan lieber am Stück liest,
findet die ausführliche Fassung mit allen Entscheidungen in `BAUPLAN-original.md`.

Rechne mit zwei bis drei Stunden, wenn der Server schon steht, und mit einer weiteren Stunde, wenn
du bei Null anfängst. Der längste Teil ist nicht die Technik, sondern das Schreiben der
Persönlichkeiten.

Schritt 0 richtet den Server ein. Wer schon einen hat, auf dem Claude Code läuft, beginnt bei
Schritt 1. Wie das Ganze bei uns zusammenhängt, also was über Claude Code läuft und was über den
Bot, steht in `WAS-LAEUFT-WORUEBER.md` daneben; das hilft beim Verstehen, bevor man anfängt.

## Schritt 0: Der Server

Wenn du noch keinen Server hast, fängst du hier an. Wir betreiben das Ganze auf einer kleinen
Maschine bei einem Cloud-Anbieter, in unserem Fall Hetzner, aber jeder andere tut es auch. Eine
eigene Maschine ist wichtig, weil das Ding rund um die Uhr läuft, Dateien schreibt und Dienste
offen hält; auf einem geteilten Webspace geht das nicht.

**Was du bestellst.** Ein kleiner Server mit zwei Kernen und vier Gigabyte Arbeitsspeicher reicht
für den Stammtisch allein. Läuft später mehr darauf, nimm acht. Als Betriebssystem Ubuntu in der
aktuellen Fassung mit Langzeitpflege; wir fahren 26.04. Rechne mit fünf bis zwanzig Euro im Monat.
Hinterlege beim Anlegen deinen öffentlichen SSH-Schlüssel, dann brauchst du nie ein Passwort.

**Die erste halbe Stunde nach dem Anlegen.** Melde dich als root an und richte dir einen eigenen
Benutzer ein, unter dem später alles läuft:

```
adduser deinname
usermod -aG sudo deinname
rsync --archive --chown=deinname:deinname ~/.ssh /home/deinname
```

Dann die Anmeldung absichern. In `/etc/ssh/sshd_config` gehören zwei Zeilen auf diesen Stand,
danach `systemctl restart ssh`:

```
PasswordAuthentication no
PermitRootLogin prohibit-password
```

Und die Firewall einschalten, nur die drei Türen, die du brauchst:

```
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

**Claude Code installieren.** Als dein Benutzer, nicht als root:

```
curl -fsSL https://claude.ai/install.sh | bash
claude
```

Beim ersten Start meldest du dich mit deinem Konto an. Es gibt auch einen Weg über npm, der native
Installer ist bequemer, weil er sich selbst aktualisiert.

**Webserver, falls du vom Handy zusehen willst.** Wir nehmen Caddy, weil er sich das Zertifikat
selbst holt und in drei Zeilen Konfiguration eine Adresse mit Passwort absichert. Ohne eigene Domain
funktioniert ein Dienst wie sslip.io, der aus der Adresse deines Servers einen Namen macht.

## Schritt 1: Voraussetzungen prüfen

Du brauchst einen Linux-Server, auf dem du dich per SSH anmelden kannst, Python in Version 3.11
oder neuer, und Claude Code, angemeldet mit deinem Abo. Ob die Anmeldung steht, verrät:

```
claude auth status
```

Kommt dort `loggedIn: true`, ist alles gut. Läuft der Stammtisch später aus einem Dienst heraus,
braucht er einen dauerhaften Zugang, weil ein Dienst sich nicht selbst anmelden kann:

```
claude setup-token
```

Das Ergebnis legst du als `CLAUDE_CODE_OAUTH_TOKEN=...` in eine Datei `~/.claude-cron-token` mit
Rechten 600. Der Motor liest sie von selbst.

## Schritt 2: Ordner und Abhängigkeiten

```
mkdir -p ~/projekte/Stammtisch ~/stammtisch-daten/runden
cd ~/projekte/Stammtisch
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn python-multipart
```

Dann den Inhalt von `software/` aus diesem Paket in den Projektordner kopieren, also `stammtisch/`,
`web/` und `deploy/`.

## Schritt 3: Pfade auf deinen Server umstellen

Der Code stammt aus einem laufenden Betrieb und enthält deshalb echte Pfade. Sie stehen in fünf
Dateien: `stammtisch/motor.py`, `stammtisch/server.py`, `stammtisch/wissen.py`,
`stammtisch/ausgabe.py` und `deploy/stammtisch.service`. Das Paket bringt dafür ein kleines Skript
mit, es liegt in `software/`:

```
cd ~/projekte/Stammtisch
bash anpassen.sh DEIN-BENUTZERNAME
```

Es ersetzt den fremden Heimatpfad durch deinen und sagt dir, was es geändert hat. Prüfe danach
einmal selbst mit `grep -rn "/home/" stammtisch/`, ob nichts übrig geblieben ist.

Zwei Dinge musst du zusätzlich von Hand entscheiden:

**Wo dein Firmenwissen liegt.** In `wissen.py` steht der Ordner, in dem gesucht wird. Bei uns ist
das ein Obsidian-Speicher, und zwar bewusst nur der Unterordner mit dem Firmenwissen, nie die
privaten Notizen. Stell das auf deinen Ordner um. Es müssen Markdown-Dateien sein.

**Wohin das Protokoll geht.** In `ausgabe.py` wird eine Notiz geschrieben, ein PDF erzeugt und eine
Zeile in ein Ereignis-Protokoll geschrieben. Die letzten beiden Wege sind hausgemacht; wenn du sie
nicht hast, kommentiere sie aus. Das Protokoll als Markdown-Datei reicht für den Anfang.

## Schritt 4: Die Persönlichkeiten anlegen

Das ist der Teil, der über die Qualität entscheidet. Jede Person ist eine Markdown-Datei. Lege sie
unter `~/.hermes/profiles/<name>/SOUL.md` ab oder stelle den Pfad in `motor.py` auf einen eigenen
Ordner um.

Im Ordner `personas/` dieses Pakets liegen zehn echte Beispiele. Der Aufbau ist immer gleich:

1. Wer die Person ist und wofür sie zuständig ist, in zwei Sätzen.
2. Wie sie arbeitet und spricht. Bei uns: Deutsch, ganze Sätze, kein Fachwort ohne Erklärung.
3. Die Fakten-Regel: Zahlen, Preise, Fristen und Paragrafen nur mit Beleg, sonst ausdrücklich
   „ohne Quelle, nur Einschätzung". Lieber eine Rückfrage als eine plausible Erfindung.
4. Die Grenzen: nichts nach außen senden, nichts löschen, Rechts- und Steuerthemen sind
   Einschätzungen und keine Beratung.
5. Wie lang das Ergebnis sein darf. Bei uns höchstens eine Seite.

Eine Person muss der Koordinator sein. Er eröffnet, verteilt das Wort, fasst zusammen und zieht das
Fazit. Die anderen decken je ein Fachgebiet ab. Fünf bis sechs Teilnehmer je Runde sind angenehm,
neun sind zu viel für ein Gespräch.

Die Zuordnung von Kurzname zu Profil, Anzeigename und Rolle steht oben in `motor.py` in drei
Zeilen. Dort trägst du deine Leute ein.

## Schritt 5: Die Gesichter

Jede Person braucht ein freigestelltes Bild als PNG mit durchsichtigem Hintergrund, dazu ein Bild
des Raums als Hintergrund. Im Ordner `bilder/` liegen unsere. Wenn du eigene willst, erzeuge sie
mit einem Bildmodell. Wichtig ist nur, dass alle Figuren im selben Stil und aus derselben
Blickrichtung erzeugt werden, sonst wirkt der Tisch zusammengewürfelt. Wir beschreiben dafür
Kleidung, Alter, Haltung und Lichtstimmung in einem Satz und hängen an jede Anfrage dieselbe
Stilbeschreibung an.

Die Bilder kommen nach `web/stammtisch/`, das Raumbild heißt `saal.jpg`. Die Sitzplätze sind in der
Oberfläche in Prozent angegeben, damit sie auf jedem Bildschirm passen.

## Schritt 6: Starten

Zum Ausprobieren im Vordergrund:

```
cd ~/projekte/Stammtisch
.venv/bin/uvicorn stammtisch.server:app --host 127.0.0.1 --port 8806
```

Läuft es, richte einen Dienst ein. Die Vorlage liegt in `deploy/stammtisch.service`. Sie startet den
Dienst nach einem Neustart von selbst wieder.

Willst du vom Handy zusehen, setze einen Webserver davor, der die Verbindung verschlüsselt und nach
einem Passwort fragt. Wir nehmen dafür Caddy. Zwei Feinheiten, die man leicht übersieht: Der
angemeldete Name wird als Kopfzeile `X-Nutzer` weitergereicht und wird zum Namen des Gastgebers.
Und wenn die Seite in einem anderen Fenster eingebettet werden soll, braucht sie die passende
Erlaubnis, sonst bleibt der Rahmen weiß.

## Schritt 7: Die erste Runde

Öffne die Seite, gib ein Thema ein, hake zwei bis vier Kollegen an und stelle drei Durchgänge ein.
Dann zuschauen.

Was du dabei beobachten solltest: Reden die Leute wirklich verschieden, oder klingen alle gleich?
Wenn alle gleich klingen, sind die Persönlichkeiten zu dünn. Gehen sie auf das ein, was der Vorredner
gesagt hat? Wenn nicht, bekommt der Sprecher zu wenig Verlauf mit.

## Schritt 8: Die Fakten-Sicherung verstehen

Ohne diesen Teil ist das Ganze gefährlich, weil ein schlüssig klingendes Fazit auf erfundener
Grundlage schlimmer ist als eine Lücke. Wir haben das nach einer Falschauskunft nachgerüstet, und es
besteht aus fünf Teilen:

**Grundwissen in jeder Runde.** Ein kurzer Steckbrief aller eigenen Firmen und Marken geht immer
mit. Ohne ihn deutet das Team unbekannte Namen frei. Bei uns hat einmal die Werberecht-Kollegin das
Alkoholwerberecht auf ein Software-Verzeichnis angewandt, weil sie nicht wusste, was das ist.

**Die Tischvorlage.** Vor der Eröffnung läuft ein eigener Durchgang, der im Netz sucht, genannte
Seiten liest, im Firmenwissen nachsieht und drei Abschnitte schreibt: worum es geht, was gesichert
ist mit Herkunft je Punkt, und was unklar bleibt. Sie erscheint als erster Eintrag im Protokoll.

**Die Herkunftspflicht.** Jede Tatsache im Gespräch trägt ihre Herkunft: aus welcher Notiz, von
welcher Webseite, aus der Tischvorlage, oder sie ist als Einschätzung gekennzeichnet.

**Der Wächter.** Ein zweites, kleines und schnelles Modell prüft jeden Beitrag gegen und meldet
unbelegte Stellen. Der Sprecher muss dann denselben Beitrag noch einmal liefern, belegt,
gekennzeichnet oder gestrichen. Was offen bleibt, steht sichtbar unter dem Beitrag.

**Die feste Prüfung.** Zitiert jemand eine Notiz, wird nachgesehen, ob es sie gibt. Erfundene
Quellenangaben fallen damit auf.

## Schritt 9: Betrieb

Die Runden liegen als JSON-Dateien auf der Platte, deshalb überlebt eine laufende Runde auch einen
Neustart des Dienstes. Trotzdem: Starte den Dienst nicht neu, während jemand eine Runde laufen hat.

Wenn du Modelle wechselst, achte auf die Kosten. Die Beiträge laufen bei uns über das Abo. Der
Wächter läuft mit einem kleinen, günstigen Modell; das reicht für seine Aufgabe.

## Was wir gelernt haben, in fünf Sätzen

Sprechblasen dürfen nicht zu schnell erscheinen, sonst kommt man beim Zuhören nicht mit; wir haben
drei Geschwindigkeiten eingebaut. Drei Sätze je Beitrag sind besser als zehn. Ein Teilnehmer, der
nur zustimmt, ist verschwendetes Geld, also gib jedem eine echte eigene Haltung. Lösch-Funktionen
testet man nie an echten Runden. Und das Wichtigste: Die Fakten-Sicherung war kein Feinschliff,
sondern der Punkt, an dem aus einer netten Spielerei ein Werkzeug wurde.
