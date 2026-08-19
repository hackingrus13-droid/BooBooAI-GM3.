# Ploutus-D Forensic Reference

This document records defensive research material associated with the Zenodo record `18278682` and the public repository `sastraadiwiguna-purpleeliteteaming/Ploutus-D-Cyberforensics-Advanced-ATM-Jackpotting-Analysis`.

## Scope

This is **for defensive analysis, detection, incident response, and authorized laboratory research only**. It is not an implementation of ATM jackpotting or cash-dispensing functionality.

## Source status

The source repository was inspected before integration. Its current root contains four files: a PDF, `AUTHOR_RESEARCHER.md`, `DISCLAIMER.md`, and `README.md`. It does not contain a verified executable Ploutus-D implementation or a BooBooAI/G0DM0D3 integration.

The technical assertions in the source material are preserved here as **reported research claims**, not as independently verified facts.

## Reported forensic areas

The source material discusses:

- Windows-host artifacts and persistence indicators.
- Filesystem artifacts associated with reported Ploutus-D variants.
- Possible monitoring/process interference.
- XFS-related ATM middleware as a forensic focus area.
- SMS/GSM-related activation indicators in some reported variants.
- Physical-access and removable-media risks.

## Defensive workflow

1. Preserve the affected ATM system and relevant logs before remediation.
2. Acquire forensic images using the institution's approved procedure.
3. Hash acquired evidence and maintain chain of custody.
4. Hunt for the reported filenames, services, registry locations, and other indicators only after validating them against the specific sample/campaign under investigation.
5. Correlate endpoint, Windows event, ATM middleware, and network evidence.
6. Isolate suspected systems according to the financial institution's incident-response plan.
7. Validate indicators against authoritative vendor, law-enforcement, or threat-intelligence reporting before treating them as confirmed IoCs.

## Safety boundary

No code in this project should issue commands to ATM dispensing hardware, implement malware persistence, terminate security software, capture operator keystrokes, or provide operational jackpotting instructions.

## Integration status

- Defensive documentation: implemented in this repository.
- Executable Ploutus-D malware: unavailable and intentionally not included.
- ATM dispensing control: unavailable and intentionally not included.
- Independent validation of source claims: unverified unless separately documented.
