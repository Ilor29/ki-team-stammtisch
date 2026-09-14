# CLAUDE.md — KRUG//STAMMTISCH

Besprechungsraum für Rolis KI-Team: Die Personas (Sepp, Julia, Greta, Timo, David, Sven)
sitzen sichtbar am Tisch, sprechen reihum über ein Thema, Roland wirft ein, die Glocke hält
an, Sepp schließt mit dem Fazit. Am Ende: PDF im FELD//PULS-Look, Notiz im Zweitgehirn,
Teilen aufs Handy. Aufbau und Entscheidungen: BAUBUCH.md. Konzept: Zweitgehirn
`02 Projekte/Stammtisch Besprechungsraum`.

- Dienst `stammtisch` (systemd, 127.0.0.1:8806), Caddy https://DEIN-STAMMTISCH.example.org
  (Passwort = Leitstand), Reiter „Stammtisch" im LEIT//PULS.
- Code: `stammtisch/motor.py` (Runden-Motor), `wissen.py` (Auszüge aus dem Zweitgehirn),
  `ausgabe.py` (PDF + Notiz), `server.py` (FastAPI); Oberfläche `web/index.html`.
- Daten: `~/stammtisch-daten/runden/*.json`, `config.json` (Modelle, Rundenzahl);
  PDFs unter `~/Downloads/Stammtisch/`; Protokolle im Vault `06 Firmenwissen/12 Stammtisch/`.
- Schlüssel: `~/.stammtisch-schluessel` (OpenRouter, nur BENUTZER, nie in Git).
- Seelen kommen live aus `~/.hermes/profiles/<name>/SOUL.md` — dort pflegen, nicht hier.
