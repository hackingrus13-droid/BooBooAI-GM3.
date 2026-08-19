#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ "${BOOBOO_ADMIN_APPROVED:-0}" != "1" ]]; then
  echo "[BOOBOO] ADMIN APPROVAL REQUIRED: export BOOBOO_ADMIN_APPROVED=1 and rerun."
  exit 77
fi
mkdir -p config state knowledge/library
if [[ ! -f config/config.json ]]; then cp config/config.example.json config/config.json; fi
if [[ ! -f config/private_rules.local.json && -f config/private_rules.local.example.json ]]; then cp config/private_rules.local.example.json config/private_rules.local.json; fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
printf '\n=== BooBooAI-GM diagnostics ===\n'
python3 -m booboo.diagnostics
printf '\n=== Starting BooBooAI-GM ===\n'
printf 'Open http://127.0.0.1:8080/ in your browser.\n\n'
exec env BOOBOO_ADMIN_APPROVED=1 python3 server.py
