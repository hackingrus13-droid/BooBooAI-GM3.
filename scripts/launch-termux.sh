#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p config state knowledge/library
if [[ ! -f config/config.json ]]; then cp config/config.example.json config/config.json; fi
if [[ ! -f config/private_rules.local.json && -f config/private_rules.local.example.json ]]; then cp config/private_rules.local.example.json config/private_rules.local.json; fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
printf '\n=== BooBooAI-GM VERIFIED WAKE UP ===\n'
python scripts/wake_up.py
printf '\n=== Starting BooBooAI-GM browser service ===\n'
printf 'Open http://127.0.0.1:8080/ in the phone browser.\n\n'
exec python server.py
