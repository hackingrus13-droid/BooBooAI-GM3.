#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
log(){ printf '\n[BOOBOO] %s\n' "$*"; }

mkdir -p config state knowledge/library models runtime
[[ -f config/config.json ]] || cp config/config.example.json config/config.json
[[ -f config/private_rules.local.json ]] || { [[ -f config/private_rules.local.example.json ]] && cp config/private_rules.local.example.json config/private_rules.local.json || true; }
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

log "BooBoo Wake Up"
python3 scripts/wake_up.py

MODEL="${BOOBOO_MODEL:-}"
if [[ -z "$MODEL" ]]; then
  for f in "$ROOT/models"/*.gguf "$HOME/models"/*.gguf "$HOME/storage/downloads"/*.gguf; do
    [[ -f "$f" ]] && { MODEL="$f"; break; }
  done
fi
LLAMA_SERVER="${BOOBOO_LLAMA_SERVER:-}"
[[ -n "$LLAMA_SERVER" ]] || { command -v llama-server >/dev/null 2>&1 && LLAMA_SERVER="$(command -v llama-server)" || true; }
[[ -n "$LLAMA_SERVER" ]] || { [[ -x "$ROOT/runtime/llama-server" ]] && LLAMA_SERVER="$ROOT/runtime/llama-server" || true; }

if [[ -z "$MODEL" || -z "$LLAMA_SERVER" ]]; then
  if [[ "${BOOBOO_AUTO_BOOTSTRAP_AI:-1}" == "1" && "$(uname -m)" == "aarch64" ]]; then
    log "No complete local AI runtime detected; starting verified bootstrap."
    if python3 scripts/bootstrap_local_ai.py; then
      [[ -n "$MODEL" ]] || MODEL="$(find "$ROOT/models" -maxdepth 1 -type f -name '*.gguf' -print -quit)"
      [[ -n "$LLAMA_SERVER" ]] || LLAMA_SERVER="$ROOT/runtime/llama-server"
    else
      log "Bootstrap did not complete. Continuing without claiming AI readiness."
    fi
  fi
fi

python3 - "$MODEL" "$LLAMA_SERVER" <<'PY'
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path
model, server = sys.argv[1], sys.argv[2]
root = Path.cwd()
def probe():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8081/v1/models', timeout=3) as r:
            d=json.loads(r.read().decode()); return bool(d.get('data')), d
    except Exception: return False, None
ok,data=probe()
if not ok and model and Path(model).is_file() and server and Path(server).is_file():
    log=root/'state/llama-server.log'; pid=root/'state/llama-server.pid'
    with log.open('ab') as out:
        p=subprocess.Popen([server,'-m',model,'--host','127.0.0.1','--port','8081','--alias','boobooai-gm'],stdout=out,stderr=subprocess.STDOUT,env=os.environ.copy(),start_new_session=True)
    pid.write_text(str(p.pid),encoding='utf-8')
    for _ in range(90):
        time.sleep(1); ok,data=probe()
        if ok: break
if ok:
    print('[BOOBOO] AI MODEL ENDPOINT: VERIFIED')
    print(json.dumps(data,indent=2)[:2000])
else:
    print('[BOOBOO] AI MODEL ENDPOINT: UNVERIFIED')
    if model: print('[BOOBOO] model=',model)
    if server: print('[BOOBOO] server=',server)
PY

log "Starting BooBooAI-GM browser service on http://127.0.0.1:8080/"
command -v termux-open-url >/dev/null 2>&1 && termux-open-url 'http://127.0.0.1:8080/' >/dev/null 2>&1 || true
exec python3 server.py
