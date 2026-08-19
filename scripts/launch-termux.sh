#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say() { printf '\n[BOOBOO] %s\n' "$*"; }

if [[ "${BOOBOO_ADMIN_APPROVED:-0}" != "1" ]]; then
  say "ADMIN APPROVAL REQUIRED: export BOOBOO_ADMIN_APPROVED=1 and rerun."
  exit 77
fi

# Install only the small, standard Termux prerequisites that this launcher
# itself requires. Model runtimes remain optional and are never fabricated.
if command -v pkg >/dev/null 2>&1; then
  missing=()
  command -v python3 >/dev/null 2>&1 || missing+=(python)
  command -v git >/dev/null 2>&1 || missing+=(git)
  command -v curl >/dev/null 2>&1 || missing+=(curl)
  if ((${#missing[@]})); then
    say "Installing missing Termux prerequisites: ${missing[*]}"
    pkg update -y
    pkg install -y "${missing[@]}"
  fi
fi

mkdir -p config state knowledge/library
if [[ ! -f config/config.json ]]; then
  cp config/config.example.json config/config.json
  say "Created config/config.json from the verified example."
fi
if [[ ! -f config/private_rules.local.json && -f config/private_rules.local.example.json ]]; then
  cp config/private_rules.local.example.json config/private_rules.local.json
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

say "Running BooBoo governance startup coverage check"
python3 scripts/governance_startup_check.py

say "Running BooBoo Wake Up verification"
python3 scripts/wake_up.py

MODEL="${BOOBOO_MODEL:-}"
if [[ -z "$MODEL" ]]; then
  for candidate in \
    "$ROOT/models/model.gguf" \
    "$ROOT/models"/*.gguf \
    "$HOME/models"/*.gguf \
    "$HOME/storage/downloads"/*.gguf; do
    if [[ -f "$candidate" ]]; then MODEL="$candidate"; break; fi
  done
fi

if [[ -n "$MODEL" && -f "$MODEL" ]] && command -v llama-server >/dev/null 2>&1; then
  if ! curl -fsS --max-time 2 http://127.0.0.1:8081/v1/models >/dev/null 2>&1; then
    say "Starting detected llama-server with the real model: $MODEL"
    nohup llama-server -m "$MODEL" --host 127.0.0.1 --port 8081 \
      >"$ROOT/state/llama-server.log" 2>&1 &
    echo $! > "$ROOT/state/llama-server.pid"
    for _ in {1..30}; do
      if curl -fsS --max-time 2 http://127.0.0.1:8081/v1/models >/dev/null 2>&1; then
        say "Local model endpoint VERIFIED."
        break
      fi
      sleep 1
    done
  else
    say "Local model endpoint already reachable."
  fi
else
  say "No verified local llama-server + GGUF model pair detected."
  say "The browser service will still start; AI inference remains UNVERIFIED until a model endpoint exists."
fi

say "Starting BooBooAI-GM browser service"
printf 'Open http://127.0.0.1:8080/ in the phone browser.\n'

if command -v termux-open-url >/dev/null 2>&1; then
  termux-open-url "http://127.0.0.1:8080/" >/dev/null 2>&1 || true
fi

exec env BOOBOO_ADMIN_APPROVED=1 python3 server.py
