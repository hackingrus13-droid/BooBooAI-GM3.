# BooBooAI-GM configuration

The repository contains only safe configuration templates. Populate private settings on the target machine.

## Private rules

Copy `private_rules.local.example.json` to `private_rules.local.json` and place your personal rules in that local file. The populated file is intentionally excluded from source control.

The application must treat the private rules file as local administrator data. It is not required for repository development and its contents do not need to be shared with the project maintainers or this chat.

## Privacy defaults

The example configuration starts in `OFFLINE` mode with cloud AI, telemetry, analytics, and third-party model providers disabled.

## Permission vocabulary

- `DENY` — capability cannot be invoked.
- `CONFIRM` — administrator confirmation is required before invocation.
- `ALLOW_LOCAL` — allowed only for configured local providers/resources.
- `ALLOW` — permitted by policy.

A capability is not considered operational merely because it is registered. It must be detected, tested, and authorized.
