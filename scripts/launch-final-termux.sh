#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
log(){ printf '\n[BOOBOO] %s\n' "$*"; }
fail(){ log "FAIL: $*"; exit 1; }

# Starting servers and installing the local runtime are privileged project
# capabilities. Require explicit administrator approval for this invocation.
if [[ "${BOOBOO_ADMIN_APPROVED:-0}" != "1" ]]; then
  echo "[BOOBOO] ADMIN APPROVAL REQUIRED: export BOOBOO_ADMIN_APPROVED=1 and rerun."
  exit 77
fi

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

MODEL_URL="http://127.0.0.1:8081/v1/models"

probe(){
  python3 - <<'PY'
import json, urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:8081/v1/models', timeout=5) as r:
        data=json.loads(r.read().decode())
    models=data.get('data') or []
    if not models:
        raise SystemExit(1)
    print('[BOOBOO] VERIFIED /v1/models')
    for item in models:
        if isinstance(item, dict) and item.get('id'):
            print('[BOOBOO] MODEL_ID='+str(item['id']))
    raise SystemExit(0)
except Exception:
    raise SystemExit(1)
PY
}

# First use an already healthy local endpoint. Never replace a working runtime.
if probe; then
  log "Existing local model endpoint is already verified."
else
  log "No verified model endpoint. Ensuring the approved local AI runtime and model exist."

  # The bootstrap performs its own official-source and SHA-256 verification.
  python3 scripts/bootstrap_local_ai.py --admin-approve \
    || fail "Verified local AI bootstrap failed."

  [[ -n "$MODEL" ]] || MODEL="$(find "$ROOT/models" -maxdepth 1 -type f -name '*.gguf' -print -quit)"
  [[ -n "$MODEL" && -f "$MODEL" ]] \
    || fail "Bootstrap completed without producing a verified GGUF model."

  [[ -n "$LLAMA_SERVER" && -x "$LLAMA_SERVER" ]] \
    || { [[ -x "$ROOT/runtime/llama-server" ]] && LLAMA_SERVER="$ROOT/runtime/llama-server" || true; }

  [[ -n "$LLAMA_SERVER" && -x "$LLAMA_SERVER" ]] \
    || fail "Bootstrap completed without a usable llama-server executable."

  log "Verified model: $MODEL"
  log "Verified server: $LLAMA_SERVER"

  PORT_OWNER="$(ss -ltnp 2>/dev/null | grep -E '127\\.0\\.0\\.1:8081|0\\.0\\.0\\.0:8081|\\[::\\]:8081' || true)"

  if [[ -n "$PORT_OWNER" ]]; then
    # A listener exists but did not answer with a valid model endpoint.
    # Only a process recorded by this project's state file may be considered
    # for controlled recovery; unknown processes are never killed.
    STATE_PID=""
    [[ -f state/llama-server.pid ]] && STATE_PID="$(cat state/llama-server.pid 2>/dev/null || true)"

    if [[ "$STATE_PID" =~ ^[0-9]+$ ]] && kill -0 "$STATE_PID" 2>/dev/null; then
      CMDLINE="$(tr '\0' ' ' < "/proc/$STATE_PID/cmdline" 2>/dev/null || true)"
      if [[ "$CMDLINE" == *llama-server* ]]; then
        log "Controlled recovery: stopping the project's recorded llama-server PID $STATE_PID."
        kill "$STATE_PID" 2>/dev/null || true
        for _ in $(seq 1 20); do
          kill -0 "$STATE_PID" 2>/dev/null || break
          sleep 1
        done
      else
        fail "8081 is occupied by a process that is not verified as the project's llama-server."
      fi
    else
      fail "8081 is occupied but its owner is not a verified project llama-server."
    fi
  fi

  : > state/llama-server.log
  nohup "$LLAMA_SERVER" \
    -m "$MODEL" \
    --host 127.0.0.1 \
    --port 8081 \
    --alias boobooai-gm \
    > state/llama-server.log 2>&1 &

  LLAMA_PID=$!
  echo "$LLAMA_PID" > state/llama-server.pid

  log "Started verified llama-server PID $LLAMA_PID."

  MODEL_READY=0
  for _ in $(seq 1 120); do
    if ! kill -0 "$LLAMA_PID" 2>/dev/null; then
      tail -n 160 state/llama-server.log 2>/dev/null || true
      fail "llama-server exited before /v1/models became ready."
    fi
    if probe; then
      MODEL_READY=1
      break
    fi
    sleep 1
  done

  [[ "$MODEL_READY" -eq 1 ]] \
    || { tail -n 160 state/llama-server.log 2>/dev/null || true; fail "Model endpoint did not become verified within 120 seconds."; }
fi

# Require an actual completion, not merely a listening port.
MODEL_ID="$(
  python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8081/v1/models', timeout=5) as r:
    data=json.loads(r.read().decode())
models=data.get('data') or []
for item in models:
    if isinstance(item, dict) and item.get('id'):
        print(item['id'])
        break
else:
    raise SystemExit(1)
PY
)" || fail "Unable to identify the loaded model."

python3 - "$MODEL_ID" <<'PY'
import json, subprocess, sys
model=sys.argv[1]
payload={
  'model': model,
  'messages':[{'role':'user','content':'Reply with exactly: BOOBOOAI_RUNTIME_VERIFIED'}],
  'stream': False,
  'temperature': 0,
}
result=subprocess.run([
  'curl','-fsS','--max-time','180',
  '-H','Content-Type: application/json',
  '-d',json.dumps(payload),
  'http://127.0.0.1:8081/v1/chat/completions',
],capture_output=True,text=True)
if result.returncode:
    raise SystemExit(f'completion request failed: {result.stderr.strip()}')
data=json.loads(result.stdout)
choices=data.get('choices') or []
if not choices:
    raise SystemExit('completion returned no choices')
choice=choices[0] or {}
message=choice.get('message') or {}
content=message.get('content')
if not isinstance(content,str) or not content.strip():
    content=choice.get('text','')
if not isinstance(content,str) or not content.strip():
    raise SystemExit('completion returned no usable text')
print('[BOOBOO] ACTUAL MODEL COMPLETION: VERIFIED')
print('[BOOBOO] RESPONSE:',content.strip()[:500])
PY

log "Starting BooBooAI-GM browser service on http://127.0.0.1:8080/"
if curl -fsS --max-time 5 http://127.0.0.1:8080/api/health >/tmp/boobooai-health.json 2>/dev/null; then
  log "Browser service already healthy."
else
  BROWSER_OWNER="$(ss -ltnp 2>/dev/null | grep -E '127\\.0\\.0\\.1:8080|0\\.0\\.0\\.0:8080|\\[::\\]:8080' || true)"
  [[ -z "$BROWSER_OWNER" ]] || fail "8080 is occupied but BooBooAI health is not verified."
  BOOBOO_ADMIN_APPROVED=1 nohup python3 server.py >state/booboo-server.log 2>&1 &
  BROWSER_PID=$!
  echo "$BROWSER_PID" > state/booboo-server.pid
  for _ in $(seq 1 60); do
    if ! kill -0 "$BROWSER_PID" 2>/dev/null; then
      tail -n 160 state/booboo-server.log 2>/dev/null || true
      fail "BooBooAI browser server exited before health verification."
    fi
    if curl -fsS --max-time 2 http://127.0.0.1:8080/api/health >/tmp/boobooai-health.json 2>/dev/null; then
      break
    fi
    sleep 1
  done
  curl -fsS --max-time 5 http://127.0.0.1:8080/api/health >/tmp/boobooai-health.json \
    || { tail -n 160 state/booboo-server.log 2>/dev/null || true; fail "Browser health verification failed."; }
fi

python3 - <<'PY'
import json
from pathlib import Path
data=json.loads(Path('/tmp/boobooai-health.json').read_text(encoding='utf-8'))
if data.get('success') is not True:
    raise SystemExit('browser health did not report success')
if not isinstance(data.get('model_endpoints_reachable'),int) or data['model_endpoints_reachable'] < 1:
    raise SystemExit('browser cannot verify a reachable model endpoint')
print('[BOOBOO] BROWSER HEALTH: VERIFIED')
PY

curl -fsS --max-time 10 http://127.0.0.1:8080/api/diagnostics >/tmp/boobooai-diagnostics.json \
  || fail "Browser diagnostics endpoint failed."

python3 - <<'PY'
import json
from pathlib import Path
data=json.loads(Path('/tmp/boobooai-diagnostics.json').read_text(encoding='utf-8'))
if data.get('success') is False:
    raise SystemExit('diagnostics reported failure')
models=data.get('models') or {}
if not isinstance(models.get('reachable'),int) or models['reachable'] < 1:
    raise SystemExit('diagnostics cannot verify a reachable model')
print('[BOOBOO] BROWSER DIAGNOSTICS: VERIFIED')
PY

command -v termux-open-url >/dev/null 2>&1 && termux-open-url 'http://127.0.0.1:8080/' >/dev/null 2>&1 || true

log "FINAL LOCAL RUNTIME VERIFICATION"
python3 scripts/final_verify.py

log "BOOBOOAI-GM3 FINAL RUNTIME STATUS: VERIFIED"
