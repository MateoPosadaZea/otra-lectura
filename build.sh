#!/usr/bin/env bash
# Genera site/ desde ediciones/*.md. Crea .venv la primera vez con el
# conversor fijado en requirements.txt; después funciona sin red.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
VENV=.venv

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Creando $VENV…"
  "$PY" -m venv "$VENV"
fi

# Reinstala solo si requirements.txt cambió desde la última instalación.
if ! cmp -s requirements.txt "$VENV/.requirements.instalados" 2>/dev/null; then
  "$VENV/bin/pip" install --quiet --disable-pip-version-check -r requirements.txt
  cp requirements.txt "$VENV/.requirements.instalados"
fi

"$VENV/bin/python" scripts/build.py
