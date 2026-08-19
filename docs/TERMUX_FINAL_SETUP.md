# BooBooAI-GM — Final Termux Setup

## One-time setup

Install Termux from a trusted/current Termux distribution, then run:

```bash
pkg update -y && pkg upgrade -y
pkg install -y git python curl
termux-setup-storage
```

Clone the project:

```bash
git clone https://github.com/hackingrus13-droid/BooBooAI-GM3. ~/BooBooAI-GM3.
cd ~/BooBooAI-GM3.
chmod +x scripts/launch-termux.sh
```

## Launch

Run:

```bash
cd ~/BooBooAI-GM3.
./scripts/launch-termux.sh
```

The launcher:

1. checks/install missing basic Termux prerequisites when `pkg` is available;
2. creates local configuration files when absent;
3. runs BooBoo Wake Up diagnostics;
4. looks only for an actually existing GGUF model;
5. starts `llama-server` automatically only when both a real GGUF model and an installed `llama-server` executable are detected;
6. verifies the local model endpoint when possible;
7. starts the browser service on `127.0.0.1:8080`;
8. opens the browser automatically when `termux-open-url` is available.

No model is invented, silently downloaded, or marked operational without a runtime response.

## Model setup

BooBooAI-GM expects an OpenAI-compatible local endpoint at:

```text
http://127.0.0.1:8081/v1
```

A common local runtime is `llama-server`. The launcher accepts an explicit model path:

```bash
export BOOBOO_MODEL="$HOME/models/your-model.gguf"
./scripts/launch-termux.sh
```

If the model endpoint is already provided by another runtime, start that runtime separately and then launch BooBooAI-GM.

## Browser

Primary interface:

```text
http://127.0.0.1:8080/
```

Health:

```bash
curl http://127.0.0.1:8080/api/health
```

Model discovery:

```bash
curl http://127.0.0.1:8081/v1/models
```

## Verification commands

```bash
python3 -m compileall -q server.py booboo scripts tests
python3 -m unittest discover -s tests -v
python3 scripts/wake_up.py
python3 scripts/sync_capabilities.py
```

## Important everyday commands

```bash
pwd                         # show current directory
ls -la                      # list files
cd ~/BooBooAI-GM3.          # enter project
./scripts/launch-termux.sh  # start BooBooAI-GM
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8081/v1/models
ps -A | grep -E 'python|llama'
ss -ltn                    # show listening TCP sockets when available
git status
git pull --ff-only
```

Stop the foreground browser server with `Ctrl-C`.

If the launcher created a model-server PID file:

```bash
if [ -f state/llama-server.pid ]; then kill "$(cat state/llama-server.pid)" 2>/dev/null || true; fi
```

## Plain-English use

The browser interface is the user-facing layer. Ask normal questions such as:

- `Explain what this error means.`
- `Check my project status.`
- `What capabilities are available right now?`
- `Search the web for current information and show the sources.`
- `Run diagnostics and tell me what is verified.`
- `Help me fix this Python error.`

The model itself determines natural-language understanding. BooBooAI-GM does not claim AI inference until the configured local model endpoint actually responds.

## Security and authorization

Security tools are discovered separately from execution. Administrator approval, configured restrictions, laboratory boundaries, and audit requirements remain enforced. An administrator approval flag cannot override a configured `DISABLED`, `UNAVAILABLE`, `READ ONLY`, `TEST ONLY`, or `AUTHORIZED LAB ONLY` state.

## Network/deep research

Ordinary web research can be performed by whatever browser/search connector is actually installed and authorized. BooBooAI-GM must report unavailable network capabilities instead of pretending they exist.

A Tor/dark-web connection is **not** automatically claimed or enabled by this repository. If a future authorized lab deployment adds a Tor-capable research adapter, it must be separately detected, permissioned, logged, and tested before being reported as available.

## Final verification rule

`VERIFIED` means an actual check succeeded. `CONFIGURED` does not mean `VERIFIED`. `NOT DETECTED` does not mean broken. `UNVERIFIED` means the current environment did not provide sufficient evidence.
