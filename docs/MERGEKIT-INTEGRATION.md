# BooBooAI-GM3 MergeKit integration

BooBooAI-GM3 integrates Arcee's MergeKit as an **optional model-engineering capability**.

## Source and pin

- Repository: https://github.com/arcee-ai/mergekit.git
- Pinned revision: `a6e402884ba9bc30da7f23e8304a35f19485de95`
- License at the pinned/current upstream source: LGPL-3.0-only
- Startup dependency: **No**
- BooBooAI capability: `model_merging`
- Authorization: administrator approval required

The source is represented as a Git submodule at `vendor/mergekit`. This keeps the
upstream project separable from BooBooAI-GM3 rather than copying its source into
the core application.

## Installation

From the BooBooAI-GM3 root:

```bash
bash scripts/install-mergekit.sh
```

The installer verifies Python >= 3.10, fetches the repository, checks out the
pinned revision, and records the revision in `state/mergekit-revision.txt`.

On Termux/Android, the installer deliberately does **not** install MergeKit's
large ML dependency stack automatically. MergeKit declares PyTorch, Transformers,
Accelerate, Safetensors and other dependencies; actual merging should be done in
a supported Linux/desktop Python environment. The BooBooAI runtime remains
functional without MergeKit.

## Supported operations

The upstream toolkit currently exposes model merging, LoRA extraction, MoE
merging, evolutionary methods, multi-stage merging, raw PyTorch merging and
tokenizer transplantation. Use the upstream CLI documentation for the exact
arguments for the selected operation.

## Safety / governance

BooBooAI never promotes a newly merged model to the active inference model merely
because a merge completed. A merge is a candidate artifact. Verify its provenance,
configuration, output integrity and inference behavior before promotion.

All execution through BooBooAI's integration is gated by `model_merging` and the
administrator approval mechanism. A hard restriction in local configuration
continues to override approval.
