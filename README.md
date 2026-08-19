# BooBooAI-GM3

BooBooAI-GM3 is a personal, administrator-governed AI platform with a local-first orchestration core. The project keeps the existing browser frontend contract while the core services are developed independently and documented by provenance.

## Current architecture

- `index.html` — existing browser frontend; preserved for compatibility.
- `server.py` — standard-library-only local orchestration server.
- `booboo/governance.py` — governed behavior, verification states, private-rule isolation, and audit support.
- `booboo/authorization.py` — administrator approval gate for privileged capabilities.
- `booboo/diagnostics.py` — safe startup diagnostics and capability reporting.
- `booboo/capabilities.py` — environment/tool discovery.
- `booboo/kali_registry.py` — evidence-based discovery against the official Kali tools catalog plus local package discovery.
- `booboo/yara_registry.py` — provenance-aware external YARA source registry and local engine detection.
- `config/governed_rules.json` — public non-secret project rules, including Kali/YARA/Colab integration rules.
- `config/rule_sources.json` — external source and license registry.
- `config/private_rules.local.json` — administrator-local rules; never commit populated private rules.
- `scripts/wake_up.py` — BooBoo Wake Up verification entry point.
- `scripts/sync_capabilities.py` — unified Kali/YARA capability inventory builder.
- `scripts/launch-termux.sh` — Termux launcher that verifies first, then starts the browser server.
- `scripts/colab_bootstrap.py` — Google Colab development/verification bootstrap with the same capability contracts.
- `tests/test_governance.py` — governance/configuration tests.
- `tests/test_capability_integrations.py` — Kali/YARA/administrator integration tests.

## Kali capability integration

The project does not hard-code an invented "600+" tool count. Kali maintains an official, changing tools catalog and metapackage system. BooBooAI-GM3 therefore discovers the current official catalog and separately discovers what the current host actually provides.

The lifecycle is:

```text
OFFICIAL KALI CATALOG
        ↓
LOCAL ENVIRONMENT DISCOVERY
        ↓
REGISTERED
        ↓
TESTED
        ↓
ADMINISTRATOR AUTHORIZED
        ↓
EXECUTION
        ↓
VERIFICATION
        ↓
AUDIT
```

Discovery does not execute tools. Privileged security tooling remains administrator-controlled.

## YARA integration

YARA is integrated as a provenance-aware detection capability. BooBooAI-GM3 does not copy external rule sets into the core repository by default. Instead it records upstream source, branch, license, and acquisition state and can synchronize sources into the local `knowledge/yara_sources/` area.

Configured sources include:

- Yara-Rules/rules — GPL-2.0.
- Neo23x0/signature-base — Detection Rule License 1.1 with per-rule metadata exceptions.
- ReversingLabs/reversinglabs-yara-rules — upstream license must be verified before redistribution.

The project can detect installed `yara`/`yarax` engines and reports their actual state. Downloading a rule set does not automatically mark it compatible or verified.

## Termux / Android

The intended phone workflow is:

```bash
cd ~/BooBooAI-GM3.
chmod +x scripts/launch-termux.sh
./scripts/launch-termux.sh
```

Open:

```text
http://127.0.0.1:8080/
```

Health check:

```bash
curl http://127.0.0.1:8080/api/health
```

Capability inventory:

```bash
python3 scripts/sync_capabilities.py
```

## Google Colab

`python scripts/colab_bootstrap.py` reports the Colab runtime, governance, Kali catalog visibility, YARA engine visibility, and project diagnostics using the same source contracts as local deployments.

The project intentionally treats free managed Colab as an ephemeral development/testing environment rather than claiming persistent hosting. Local/Termux and Colab share the same source tree and verification contracts, while each environment independently reports its actual capabilities.

## Local model requirement

BooBooAI-GM3 does not fabricate model availability. A local OpenAI-compatible model server must actually be running before `/v1/ultraplinian/completions` can return an AI response.

The default endpoint is:

```text
http://127.0.0.1:8081/v1
```

## Verification

Run locally:

```bash
python3 -m compileall -q server.py booboo scripts tests
python3 -m unittest discover -s tests -v
python3 -m booboo.diagnostics
python3 scripts/sync_capabilities.py
```

GitHub Actions performs syntax, configuration, governance, integration, diagnostics, and required-file checks on pushes to `main` and pull requests.

A passing syntax or unit test does not by itself prove that a local AI model, GPU, network, Android-specific capability, Kali tool, or YARA engine is operational. Those require actual runtime evidence from the target environment.
