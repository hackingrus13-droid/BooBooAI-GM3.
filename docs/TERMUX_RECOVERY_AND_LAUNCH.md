# Termux recovery and final launch

## Symptom

If `curl` reports `CANNOT LINK EXECUTABLE "curl": cannot locate symbol "SSL_set_quic_tls_transport_params"`, the Termux package set is inconsistent. This is a host-package problem, not a BooBooAI-GM application error.

## Repair

Run these commands exactly, without trailing backticks:

```bash
termux-change-repo
```

Select a current **Main Repository** mirror, then:

```bash
apt update
apt full-upgrade -y
apt install --reinstall openssl libngtcp2 libcurl curl
```

If `apt update` itself cannot start because the HTTPS transport is broken, use the current Termux recovery procedure for the installed Termux distribution rather than deleting project files. A rolling Termux installation should be kept fully upgraded before adding more packages.

## Update BooBooAI-GM

The existing clone in `~/BooBooAI-GM3.` means `git clone` must not be run again.

```bash
cd ~/BooBooAI-GM3.
git status
git pull --ff-only
```

## Final launcher

```bash
cd ~/BooBooAI-GM3.
bash scripts/launch-final-termux.sh
```

The final launcher:

1. runs startup diagnostics;
2. searches for an existing GGUF model;
3. searches for an existing `llama-server`;
4. if both are absent on Android arm64, attempts the verified local-AI bootstrap;
5. downloads only the explicitly recorded upstream llama.cpp Android arm64 archive and the Qwen 0.5B Q4_K_M fallback model;
6. verifies SHA-256 before using either download;
7. starts `llama-server` on `127.0.0.1:8081`;
8. verifies `/v1/models` before reporting AI readiness;
9. starts BooBooAI-GM on `127.0.0.1:8080`;
10. opens the browser when `termux-open-url` is available.

## Existing larger model

If you already have a GGUF model, put it in:

```text
~/BooBooAI-GM3./models/
```

or:

```text
~/models/
```

The launcher prefers an existing model over the small fallback.

## Verification

```bash
python3 scripts/wake_up.py
python3 -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8081/v1/models", timeout=5).read().decode())'
python3 -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8080/api/health", timeout=5).read().decode())'
```

## Important

Do not type a trailing backtick (`) after shell commands. A trailing backtick starts shell command substitution and causes the `>` continuation prompt seen in the failed session.

Do not run `git clone` again when `~/BooBooAI-GM3.` already exists.
