# Was läuft über Claude Code, was über Hermes, was über nichts von beidem

Stand 14.09.2026, geprüft an den laufenden Dateien, nicht aus dem Gedächtnis geschrieben. Roland hat
gefragt, weil die beiden Namen im Haus durcheinandergehen: „was läuft über Hermes, was über Claude
Code, detailliert aufgearbeitet."

Die kurze Antwort: **Claude Code ist unser Arbeiter, Hermes ist unser Pförtner und unsere
Pinnwand.** Alles, was denkt und baut, läuft über Claude Code und damit über Rolis Abo. Hermes
nimmt Nachrichten entgegen, hält die Aufgabentafel und bewahrt die Persönlichkeiten auf.

## Über Claude Code läuft

**Die Karten.** Jede Projekt-Sitzung in der Relay-App ist ein laufendes Claude Code, interaktiv, mit
eigenem Ordner und eigener Anweisungsdatei. Brain, Skillkontor, Krugmeister-Brain, Medienwerk und
die übrigen.

**Der Stammtisch.** Jeder Redebeitrag ist ein eigener Aufruf `claude -p` mit der Persönlichkeit als
zusätzlicher Systemanweisung. Die Runden laufen mit einem schnellen Modell, das Fazit mit einem
stärkeren. Der Fakten-Wächter ist ein weiterer, sehr kleiner Aufruf mit festem Antwortformat.

**Der Abo-Läufer.** Er holt Aufgaben von der Tafel und lässt sie über `claude -p` bearbeiten, mit
der Persönlichkeit der zuständigen Person und, wenn auf der Aufgabe steht, welche Fachkraft es sein
soll, mit deren Rollenbeschreibung.

**Ein Teil der Automatiken.** Überall dort, wo etwas beurteilt oder formuliert werden muss, etwa
beim Postfach-Agenten oder bei Kennzahlen-Texten.

Bezahlt wird das über das Abo, nicht über Guthaben. Für Läufe ohne Mensch liegt ein dauerhafter
Zugang in einer Datei mit Rechten 600, weil ein Dienst sich nicht selbst anmelden kann.

## Über Hermes läuft

**Der Telegram-Bot.** Das Gespräch im Chat läuft über ein günstiges fremdes Modell, bezahlt aus dem
OpenRouter-Guthaben, nicht über das Abo. Das ist bewusst so: kurze Zurufe und Rückfragen sollen nicht
das Abo belasten.

**Die Aufgabentafel.** Anlegen, zuweisen, kommentieren, abschließen. Die Tafel verteilt nicht selbst
an Modelle; sie ist eine Pinnwand, von der sich der Abo-Läufer bedient.

**Die Personalakte.** Die Persönlichkeiten liegen als Textdatei je Person in den Hermes-Profilen. Der
Stammtisch liest dieselben Dateien, damit es nur eine Wahrheit gibt. Deshalb wirkt Hermes an
Stellen mit, wo gar kein Hermes läuft.

## Über keines von beidem läuft

Die meisten Wachen und Erinnerungen sind schlichte Python-Skripte, die nichts fragen und nur messen
und melden: Server-Wache, Speicheralarm, Update-Wache, Rechnungserinnerung, Neustart-Erinnerung,
Hetzner-Wächter, Ideen-Bot, Job-Späher. Sie schicken ihre Meldungen über denselben Telegram-Bot,
haben mit Hermes aber sonst nichts zu tun. Das ist der häufigste Irrtum: Eine Telegram-Nachricht
heißt nicht, dass Hermes gearbeitet hat.

## Die Trennlinie in einem Satz

Kommt eine Nachricht auf Telegram an oder geht eine hinaus, ist der Bot beteiligt. Wird dabei
gedacht, gebaut oder geschrieben, war es Claude Code.

## Was wir über Claude Code selbst festgehalten haben

Die komplette Dokumentation ist am 05.09.2026 ausgewertet worden, 191 Seiten, vier Leser, je ein
Viertel. Das Ergebnis steht in [[claude-code-doku-auswertung-2026-09-05]]: was wir davon nutzen
(Hooks, Ausgabestile, Plugins, kopflose Aufrufe, Sitzungen) und was wir bewusst liegen lassen. Dazu
kommen die Funde aus der Anleitungssammlung in [[claude-bibliothek-2026-09-14]], darunter die
Steuerung der Denktiefe je Aufgabe und die Übergabedatei zwischen Sitzungen.

Eine vollständige Bedienungsanleitung für Claude Code haben wir bewusst nicht abgeschrieben; die
steht beim Hersteller und veraltet schneller, als wir sie pflegen könnten. Was bei uns liegt, ist
die Auswertung: was davon für unsere Arbeitsweise taugt.
