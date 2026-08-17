# BooBooAI-GM provenance standard

This file establishes how BooBooAI-GM records originality without claiming ownership of external software or model assets.

## Categories

| Category | Meaning | Repository treatment |
|---|---|---|
| `ORIGINAL` | Code/design authored specifically for BooBooAI-GM | Project source |
| `DEPENDENCY` | External software/library/runtime | Isolated, licensed, documented |
| `MODEL_ASSET` | Externally produced model weights | License/provenance recorded |
| `REFERENCE` | External documentation/research/project studied for knowledge | Citation/reference only |
| `USER_PRIVATE` | Administrator rules, credentials, private data | Never committed |

## Rule

No external component is represented as BooBooAI-GM original code merely because it is integrated into the system.

The core architecture, policy system, orchestration, registry, diagnostics, memory, knowledge system, model abstraction, routing contracts, communications abstraction, verification system, audit/recovery system, and browser interface are intended to be independently implemented for this project.

## Verification

Before a component is marked `ORIGINAL`, its source history and implementation should be reviewed for accidental copied code, incompatible licensing, or unattributed third-party material. Unknown provenance is recorded as `UNVERIFIED` rather than guessed.
