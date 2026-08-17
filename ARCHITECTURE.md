# BooBooAI-GM architecture

**Project identity:** BooBooAI-GM — Autonomous Research & Development Intelligence Platform

## Design principles

1. Local-first: the core remains usable without Internet connectivity.
2. Privacy-first: cloud, telemetry, analytics, and third-party providers are opt-in capabilities.
3. Administrator-controlled: permissions are explicit and evaluated before privileged execution.
4. Verification-first: discovered capabilities are not claimed operational until tested.
5. Original implementation: existing projects may be studied for engineering techniques, but BooBooAI-GM maintains its own architecture, code, configuration, identity, and UI.
6. Provenance: original code, third-party dependencies, and external references are recorded separately.
7. Replaceable providers: model/runtime/cloud components are adapters rather than hard dependencies of the core.
8. Recoverable state: configuration changes are versioned so rollback can be implemented without exposing private rules.

## Execution pipeline

```text
User request
  -> BooBooAI reasoning/orchestration
  -> Policy & Permission Engine
  -> Capability discovery/registry
  -> Tool/Terminal/Network/Database capability
  -> Execution
  -> Verification
  -> Result + audit record
```

Privileged operations require the policy engine to return an authorization decision before execution. A `DENY` decision is terminal. A `CONFIRM` decision requires the configured administrator confirmation mechanism.

## Boot pipeline

```text
BOOT
 -> SELF-DIAGNOSTICS
 -> HARDWARE DISCOVERY
 -> DEPENDENCY CHECK
 -> MODEL CHECK
 -> TOOL REGISTRY CHECK
 -> NETWORK CHECK
 -> KNOWLEDGE CHECK
 -> PERMISSION CHECK
 -> TEST
 -> REPORT
 -> READY
```

Unverified capabilities remain explicitly `UNVERIFIED`.

## Capability lifecycle

```text
Available -> Installed -> Registered -> Tested -> Authorized
```

These states are independent. A tool can be installed but untested, or registered but unauthorized.

## Communications

The planned Universal Communications Abstraction Layer (UCAL) keeps transport and hardware-specific code outside the AI core. Adapters can represent Ethernet, Wi-Fi, Bluetooth, cellular, serial/USB, RFID/NFC, IR, and radio/SDR resources when the host hardware, drivers, protocols, permissions, and applicable regulations support them.

## Local AI stack

The intended target stack is compatible with:

```text
Laptop/desktop
 -> Linux/Kali or Windows + Linux
 -> Ollama or another local OpenAI-compatible runtime
 -> Open WebUI and/or BooBooAI-GM UI
 -> local open-weight models
 -> BooBooAI-GM policy/orchestration layer
 -> local tools/knowledge/memory
```

Ollama and Open WebUI remain replaceable integrations. The project must not assume that a particular runtime or model is installed until discovery verifies it.

## Security laboratory

Security tooling is represented through the same registry and policy system as other tools. The project does not claim a fixed number of integrated Kali tools. Actual installed tools are discovered and recorded individually with executable path, version, documentation reference, permissions, and test status.

Kali itself provides metapackages for grouped tool installation, including `kali-linux-everything`, but a metapackage is not evidence that every binary is installed, working, or authorized on a particular host.

## Private administrator rules

Private rules are intentionally external to repository source. The repository provides a schema/template only. The populated local file is excluded by `.gitignore` and is not required to be disclosed to the development assistant.
