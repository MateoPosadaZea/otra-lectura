#!/usr/bin/env bash
# Build + commit + push. Cloudflare Pages publica site/ al recibir el push.
set -euo pipefail
cd "$(dirname "$0")"

./build.sh

git add -A ediciones site
if git diff --cached --quiet; then
  echo "Sin cambios que publicar."
  exit 0
fi

mensaje="${1:-Publica ediciones ($(date +%Y-%m-%d))}"
git commit -m "$mensaje"
git push -u origin "$(git rev-parse --abbrev-ref HEAD)"
