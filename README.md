# KRUG//STAMMTISCH — ein Besprechungsraum im Browser, in dem KI-Kollegen miteinander reden

![Eine laufende Runde: der Koordinator hat das Wort, zwei Fachkräfte auf Zeit sind dazugekommen](bilder/oberflaeche/1-buehne-mit-gespraech.png)

Dieses Paket enthält einen kompletten, seit Wochen laufenden Anwendungsfall: neun KI-Kollegen mit
eigenem Charakter, eigenem Gesicht und eigenem Fachgebiet sitzen an einem Tisch und besprechen ein
Thema, das der Gastgeber vorgibt. Man sieht ihnen dabei zu, kann dazwischenreden, Unterlagen auf den
Tisch legen und eine Pause einlegen. Am Ende entstehen ein Protokoll, ein PDF und eine Notiz im
eigenen Wissensspeicher.

Gebaut von Roland (Einzelstein Software) für seine eigenen Firmen, im Einsatz seit dem 4. September 2026.

## Was wirklich drin ist

Kein Video, keine Präsentation, sondern der laufende Code, die neun Persönlichkeiten im Wortlaut,
alle Figuren als Bilddateien und zwei Anleitungen. Wer das nachbauen will, kann das mit diesem
Paket tun.

```
README.md             diese Datei
ANLEITUNG.md          Schritt für Schritt vom leeren Server zur ersten Runde
WAS-LAEUFT-WORUEBER.md  wie das Ganze zusammenhängt: was über Claude Code läuft,
                      was über den Telegram-Bot, was reine Messskripte sind
BAUPLAN-original.md   die ausführliche Bauanleitung mit allen Entscheidungen und Fallen
software/             der Code: Motor, Wissenssuche, Ausgabe, Dienst, Oberfläche
personas/             die zehn Persönlichkeiten als Textdateien, so wie sie im Betrieb laufen
bilder/               die Figuren, der Raum, die Fachkräfte-Porträts und zwei
                      Bildschirmfotos der laufenden Oberfläche
fachkraefte/          82 Rollen, die man für eine einzelne Aufgabe dazuholen kann,
                      dazu unser deutsches Personalverzeichnis und die Lizenz
beispiel/             eine echte Runde zum Mitlesen, als Text und als PDF
```

## Was daran das Interessante ist

**Neun feste Personen, dazu 82 Fachkräfte auf Zeit.** Am Tisch sitzen der Koordinator und die
Fachleute für Recht, Finanzen, Marketing, Export, Logistik, Vertrieb, Design und Technik. Verlangt
ein Thema mehr, holt der Koordinator von selbst eine Fachkraft dazu, etwa einen
Kurzvideo-Schnittlehrer. Auf dem ersten Bildschirmfoto sieht man genau das.

**Die Kollegen reden miteinander, nicht mit dir.** Jeder Beitrag ist ein eigener Modellaufruf mit
eigener Persönlichkeit. Der Koordinator eröffnet, verteilt das Wort, fasst zwischendurch zusammen
und zieht am Ende ein Fazit. Du kannst jederzeit dazwischenrufen, dann geht der nächste Sprecher
zuerst darauf ein.

**Sie erfinden nichts.** Das ist der aufwendigste Teil und der Grund, warum das Ding brauchbar ist
statt nur hübsch. Vor jeder Runde wird eine Tischvorlage erstellt: ein eigener Durchgang sucht im
Netz, liest die genannten Seiten, sieht im eigenen Firmenwissen nach und schreibt auf, was gesichert
ist und was unklar bleibt. Jede Tatsache im Gespräch braucht eine Herkunft. Ein zweites, kleines
Modell prüft jeden Beitrag gegen und schickt ihn zurück, wenn etwas unbelegt ist. Was trotzdem offen
bleibt, steht sichtbar unter dem Beitrag.

**Es kostet fast nichts.** Die Runden laufen über das normale Abo, nicht über bezahlte Aufrufe. Eine
Runde mit fünf Teilnehmern und drei Durchgängen dauert je nach Tempo zehn bis zwanzig Minuten.

**Vorlesen, weil lange Gespräche am Handy anstrengend sind.** Jeder Beitrag hat einen kleinen
Lautsprecher, und oben im Protokoll sitzt ein Knopf, der die ganze Runde nacheinander vorliest, mit
Stopp und mitlaufendem Bildlauf. Das läuft über einen lokalen Vorlese-Dienst auf der eigenen
Maschine, nichts davon geht ins Netz. Weil es nur eine deutsche Stimme gibt, sagt der Vorleser vor
jedem Beitrag, wer spricht.

**Eingeben wie im Messenger.** Das Eingabefeld hat Mikrofon, Anhang, einen Knopf zum Glätten des
Diktats (Füllwörter und Verhörer raus) und ein Kreuz, das das Feld in einem Griff leert. Das
Gelöschte bleibt acht Sekunden zurückholbar, damit ein Fehlgriff am Handy kein langes Diktat
frisst. Während ein Diktat läuft, verwirft dasselbe Kreuz nur das Diktat und stellt her, was vorher
im Feld stand.

## Was du dafür brauchst

Einen kleinen Linux-Server, auf dem Claude Code angemeldet ist. Python. Einen Ordner mit Notizen,
aus dem die Kollegen ihr Firmenwissen ziehen. Mehr nicht. Ein Webserver davor ist empfehlenswert,
wenn du vom Handy zusehen willst.

Zwei Dinge sind freiwillig. Das **Vorlesen** braucht einen Vorlese-Dienst auf derselben Maschine,
der auf `127.0.0.1:5005` einen kurzen Text annimmt und eine WAV-Datei zurückgibt; wir benutzen dafür
Piper mit einer deutschen Stimme. Fehlt der Dienst, bleibt der Rest vollständig nutzbar, nur der
Lautsprecher antwortet nicht. Das **Diktat** im Eingabefeld ist die Spracherkennung des Browsers,
läuft also nur in Chrome und schickt den Ton an Google; wer das nicht will, tippt.

Und eines ist kein Muss, aber eine Entscheidung wert: Der Motor kann die Beiträge entweder über das
**angemeldete Abo** erzeugen (so läuft es bei uns) oder über einen bezahlten Dienst als Ausweichweg,
wenn das Abo gerade nicht kann. Beides steht in einer Einstellung, standardmäßig ist das Abo gewählt.

## Eine ehrliche Einordnung

Der Stammtisch ersetzt keine Recherche und kein Fachgespräch mit Menschen. Er ist gut darin, einen
Gedanken von fünf Seiten zu beleuchten, blinde Flecken sichtbar zu machen und in zwanzig Minuten ein
Protokoll zu erzeugen, das man sonst nie geschrieben hätte. Er ist schlecht darin, Neues zu wissen,
das nicht in deinen Notizen oder im Netz steht.

Die Rechts- und Steuerbeiträge sind Einschätzungen, keine Beratung. Das steht auch so in den
Persönlichkeiten drin und wird eingehalten.

## Lizenz und Weitergabe

Alles Weitere steht in `LIZENZ.md`: MIT für Software und Anleitungen, MIT für die Rollen mit dem
Vermerk des Ursprungsverzeichnisses, dazu ein Wort zu Bildern und Persönlichkeiten.

Code und Anleitungen darfst du frei verwenden und verändern, auch geschäftlich. Die Bilder sind mit
einem Bildmodell erzeugt und für diesen Anwendungsfall gedacht; für eine eigene Firma würde ich
eigene Figuren erzeugen lassen, dann passen sie zur eigenen Marke. Die Persönlichkeiten beziehen
sich auf eine bestehende Firma, sie sind als Muster gedacht und nicht zum Kopieren.

Fragen? Dann frag den, der dir dieses Paket gegeben hat.
