#!/usr/bin/env bash
# Randeaza _build/og/<lang>.html -> img/og-<lang>.jpg (1200x630).
#
#   node _build/og.mjs && bash _build/og-shot.sh
#
# Scala 1 si --virtual-time-budget sunt obligatorii: la scala 2 se schimba
# antialiasingul textului, iar fara virtual-time chromium fotografiaza inainte
# sa se incarce Plus Jakarta Sans de la Google Fonts si iese alt font.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROME="${CHROME:-$HOME/.cache/ms-playwright/chromium-1134/chrome-linux/chrome}"
PORT=8731
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

(cd "$ROOT" && python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1) &
SRV=$!
trap 'kill $SRV 2>/dev/null; rm -rf "$TMP"' EXIT
sleep 1

for l in "${@:-ro en de hu fr nl da sv}"; do
  for lang in $l; do
    "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
      --virtual-time-budget=20000 --window-size=1200,630 \
      --screenshot="$TMP/$lang.png" "http://127.0.0.1:$PORT/_build/og/$lang.html" >/dev/null 2>&1
    convert "$TMP/$lang.png" -sampling-factor 2x2,1x1,1x1 -quality 88 -strip "$ROOT/img/og-$lang.jpg"
    cp "$ROOT/img/og-$lang.jpg" "$ROOT/_build/img-original/og-$lang.jpg"
    echo "  og-$lang.jpg"
  done
done
