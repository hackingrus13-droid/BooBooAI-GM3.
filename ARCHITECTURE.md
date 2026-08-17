# BooBooAI-GM — Original Architecture

**Project identity:** BooBooAI-GM — Autonomous Research & Development Intelligence Platform

## Originality standard

BooBooAI-GM is to be developed as an independently authored project from the ground up. Existing projects, documentation, protocols, algorithms, runtimes, and research may be studied to understand engineering techniques, but their code, branding, project structure, or implementation is not to be represented as BooBooAI-GM's original work.

The project maintains this provenance distinction:

```text
ORIGINAL BOOBOOAI-GM CODE
        !=
EXTERNAL INFRASTRUCTURE / DEPENDENCY
        !=
REFERENCE / INSPIRATION
```

The goal is independent implementation, not a claim that no other person could ever independently invent a similar concept. Similarity alone is not evidence of copying.

## Core ownership boundary

The BooBooAI-GM core must not require a third-party AI application, agent framework, web UI, model router, policy engine, memory system, tool registry, or orchestration framework to define its identity or architecture.

External components may be connected through explicitly isolated adapters when useful or necessary, but those adapters are not the BooBooAI-GM core. Removing an optional external provider must not destroy the project's architecture.

The operating system, hardware drivers, compiler/runtime, model weights, and other system-level infrastructure are treated as external infrastructure rather than BooBooAI-GM source code. Their licenses and provenance must be recorded separately.

## Original core layers

```text
BooBooAI-GM
│
├── Original AI Core
│   ├── model abstraction
│   ├── model router
│   ├── reasoning/orchestration
│   ├── task planner
│   └── verification engine
│
├── Original Administrator System
│   ├── policy engine
│   ├── permission engine
│   ├── roles
│   ├── configuration versioning
│   └── rollback/recovery
│
├── Original Knowledge System
│   ├── local library
│   ├── indexing
│   ├── retrieval
│   ├── RAG orchestration
│   └── update pipeline
│
├── Original Tool System
│   ├── capability discovery
│   ├── registry
│   ├── metadata
│   ├── authorization
│   └── testing
│
├── Original Execution System
│   ├── terminal abstraction
│   ├── filesystem abstraction
│   ├── database abstraction
│   ├── server abstraction
│   └── execution/verification loop
│
├── Original Communications Layer
│   └── UCAL transport abstraction
│
├── Original Memory System
├── Original Diagnostics
├── Original Audit/Recovery System
└── Original Browser Interface
```

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

Privileged operations require an authorization decision before execution. `DENY` is terminal. `CONFIRM` requires the configured administrator confirmation mechanism. Authorization does not falsely imply that a capability is installed or functional.

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

A capability that cannot be tested remains explicitly `UNVERIFIED`. Later startup or scheduled diagnostics may retest it.

## Capability lifecycle

```text
Available -> Installed -> Registered -> Tested -> Authorized
```

These states are independent. A tool can be installed but untested, or registered but unauthorized.

## Communications

The Universal Communications Abstraction Layer (UCAL) keeps transport and hardware-specific code outside the AI core. It can represent Ethernet, Wi-Fi, Bluetooth, cellular, serial/USB, RFID/NFC, IR, and radio/SDR resources when host hardware, drivers, protocols, permissions, and applicable regulations support them.

## Model and runtime strategy

The original core owns the model abstraction and routing contracts. Local runtimes such as Ollama can be supported as adapters; Open WebUI can be supported as an optional external interface/provider integration. Neither is the BooBooAI-GM core.

Local open-weight model files are external model assets and retain their own license/provenance information. BooBooAI-GM provides the original orchestration, configuration, routing, permissions, diagnostics, and interface around them.

Optional cloud model providers can be connected through provider adapters. Cloud availability must never be confused with local capability.

## Security laboratory

Security tooling is represented through the same registry and policy system as other tools. BooBooAI-GM does not claim a fixed number of integrated Kali tools merely because Kali provides a large tool collection. Actual installed tools are discovered and recorded individually with executable path, version, documentation reference, permissions, and test status.

## Provenance ledger

Every material component should eventually be classified as one of:

- `ORIGINAL` — authored specifically for BooBooAI-GM.
- `DEPENDENCY` — external software/library/runtime required or optionally connected.
- `MODEL_ASSET` — externally produced model weights with their own license.
- `REFERENCE` — documentation, research, or project studied for engineering knowledge.
- `USER_PRIVATE` — administrator data that must not be committed or exposed.

This ledger is part of the project's verification standard.

## Private administrator rules

Private rules are intentionally external to repository source. The repository provides a schema/template only. The populated local file is excluded by `.gitignore` and is not required to be disclosed to the development assistant.
