# BooBooAI-GM3

BooBooAI-GM3 is a personal, administrator-governed AI platform with a local-first orchestration core. The project keeps the existing browser frontend contract while the core services are developed independently and documented by provenance.

## Current verified architecture

- `index.html` — existing browser frontend; preserved for compatibility.
- `server.py` — standard-library-only local orchestration server.
- `booboo/governance.py` — governed behavior, verification states, private-rule isolation, and audit support.
- `booboo/diagnostics.py` — safe startup diagnostics and capability reporting.
- `booboo/capabilities.py` — environment/tool discovery.
- `config/governed_rules.json` — public non-secret project rules.
- `config/private_rules.local.json` — administrator-local rules; never commit populated private rules.
- `scripts/wake_up.py` — BooBoo Wake Up verification entry point.
- `scripts/launch-termux.sh` — Termux launcher that verifies first, then starts the browser server.
- `scripts/colab_bootstrap.py` — Google Colab development/verification bootstrap.
- `tests/test_governance.py` — governance and configuration tests.

## Governance model

The core behavior policy requires evidence before verification claims, distinguishes documented facts from inference, records failures, avoids repeating known failed approaches without new evidence, and keeps private administrator rules local.

Administrator control applies to this project's approved configuration and permissions. It does not authorize bypassing host-platform restrictions, authentication, law, safety controls, or third-party service policies. Security research is intended for owned, isolated, or explicitly authorized environments.

## Termux / Android

The intended phone workflow is:

```bash
cd ~/BooBooAI-GM3.
chmod +x scripts/launch-termux.sh
./scripts/launch-termux.sh
```

The launcher performs the verified wake-up sequence and then starts the local server on `127.0.0.1:8080`.

Open:

```text
http://127.0.0.1:8080/
```

Health check:

```bash
curl http://127.0.0.1:8080/api/health
```

Governance report:

```text
http://127.0.0.1:8080/api/governance
```

Model discovery:

```text
http://127.0.0.1:8080/api/models
```

Diagnostics:

```text
http://127.0.0.1:8080/api/diagnostics
```

## Local model requirement

BooBooAI-GM3 does not fabricate model availability. A local OpenAI-compatible model server must actually be running before `/v1/ultraplinian/completions` can return an AI response.

The default endpoint is:

```text
http://127.0.0.1:8081/v1
```

For Termux, the `llama-cpp` package exists in the Termux package ecosystem, but the actual package availability, device architecture, memory requirements, model size, and runtime performance must be checked on the device before claiming a working local model.

## Google Colab

`python scripts/colab_bootstrap.py` can be used inside a Colab checkout for development and verification.

Free managed Colab is not treated as persistent web hosting. Google documents that free resources are dynamic and not guaranteed, and managed runtimes restrict several forms of persistent/remote web-service use. Therefore BooBooAI-GM3 uses Colab as a development/testing environment and Termux or other user-controlled hardware as the persistent localhost browser environment.

## Model racing

The existing frontend tiers remain:

- Fast — up to 12 configured endpoints
- Balanced — up to 20 configured endpoints
- Smart — up to 27 configured endpoints

Only endpoints that actually respond are counted as reachable. The baseline race score is deterministic and transparent; it is not represented as a reliable semantic judge.

## Verification

Run locally:

```bash
python3 -m compileall -q server.py booboo scripts
python3 -m unittest discover -s tests -v
python3 -m booboo.diagnostics
```

GitHub Actions performs the same class of syntax, configuration, governance, diagnostics, and required-file checks on pushes to `main` and pull requests.

A passing syntax or unit test does not by itself prove that a local AI model, GPU, network, or Android-specific capability is operational. Those require actual runtime evidence.
