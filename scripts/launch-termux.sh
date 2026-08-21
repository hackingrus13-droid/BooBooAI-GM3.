#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say() { printf '\n[BOOBOO] %s\n' "$*"; }
fail() { say "FAIL: $*" >&2; exit 1; }

if [[ "${BOOBOO_ADMIN_APPROVED:-0}" != "1" ]]; then
  say "ADMIN APPROVAL REQUIRED: export BOOBOO_ADMIN_APPROVED=1 and rerun."
  exit 77
fi

# Install only prerequisites needed to perform the governed startup checks.
if command -v pkg >/dev/null 2>&1; then
  missing=()
  command -v python3 >/dev/null 2>&1 || missing+=(python)
  command -v git >/dev/null 2>&1 || missing+=(git)
  command -v curl >/dev/null 2>&1 || missing+=(curl)
  command -v ss >/dev/null 2>&1 || true
  if ((${#missing[@]})); then
    say "Installing missing Termux prerequisites: ${missing[*]}"
    pkg update -y
    pkg install -y "${missing[@]}"
  fi
fi

mkdir -p config state knowledge/library models runtime
[[ -f config/config.json ]] || cp config/config.example.json config/config.json
if [[ ! -f config/private_rules.local.json && -f config/private_rules.local.example.json ]]; then
  cp config/private_rules.local.example.json config/private_rules.local.json
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

say "Running governance startup coverage check"
python3 scripts/governance_startup_check.py

# launch-final-termux.sh is the single authoritative Termux runtime path. It
# performs Wake Up, verified llama.cpp/model bootstrap, /v1/models, real
# inference, browser health, diagnostics, and the project final verifier.
# Keeping one runtime path prevents the older launcher from starting a browser
# with an unverified model endpoint.
exec "$ROOT/scripts/launch-final-termux.sh"
