#!/bin/bash
# Stellt die Pfade im Stammtisch-Code auf deinen Benutzernamen um.
# Aufruf im Projektordner:  bash anpassen.sh DEIN-BENUTZERNAME
set -e

NEU="$1"
ALT="BENUTZER"

if [ -z "$NEU" ]; then
  echo "So geht es:  bash anpassen.sh DEIN-BENUTZERNAME"
  echo "Beispiel:    bash anpassen.sh anna"
  exit 1
fi

if [ "$NEU" = "$ALT" ]; then
  echo "Dein Benutzername ist derselbe wie im Original, es gibt nichts zu tun."
  exit 0
fi

GEAENDERT=0
for datei in stammtisch/*.py web/index.html deploy/*.service; do
  [ -f "$datei" ] || continue
  if grep -q "/home/$ALT" "$datei"; then
    ANZAHL=$(grep -c "/home/$ALT" "$datei")
    sed -i "s|/home/$ALT|/home/$NEU|g" "$datei"
    sed -i "s|User=$ALT|User=$NEU|g; s|Group=$ALT|Group=$NEU|g" "$datei"
    echo "$datei: $ANZAHL Stellen umgestellt"
    GEAENDERT=$((GEAENDERT + ANZAHL))
  fi
done

echo
echo "Fertig, $GEAENDERT Stellen insgesamt."
echo
echo "Zwei Dinge musst du noch von Hand entscheiden:"
echo "  1. In stammtisch/wissen.py: der Ordner, in dem dein Firmenwissen liegt."
echo "  2. In stammtisch/ausgabe.py: wohin Protokoll und PDF gehen sollen."
echo
echo "Gegenprobe, ob nichts Fremdes übrig ist:"
echo "  grep -rn \"/home/$ALT\" stammtisch/ web/ deploy/"
