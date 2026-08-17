# BooBooAI-GM3

BooBooAI-GM3 is the project name for the existing G0DM0DƎ / ULTRAPLINIAN interface and its local orchestration layer.

## Current architecture

- `index.html` — existing frontend UI; preserved rather than replaced.
- `server.py` — standard-library-only local orchestration server.
- `/v1/info` — reports the running engine and configured endpoints.
- `/v1/ultraplinian/completions` — frontend-compatible Server-Sent Events endpoint.
- Local model servers — any OpenAI-compatible `/v1/chat/completions` provider can be registered.

## Local-first setup

The orchestrator listens on `127.0.0.1:8080` by default. The default model endpoint is `127.0.0.1:8081` so the two services do not collide.

### 1. Start a local model server

For llama.cpp, start an OpenAI-compatible server on port 8081. The exact model path depends on the model you have installed.

Example shape:

```bash
llama-server -m /path/to/model.gguf --port 8081
```

### 2. Start BooBooAI-GM3

```bash
python3 server.py
```

Then open:

```text
http://127.0.0.1:8080/
```

Check the backend with:

```text
http://127.0.0.1:8080/v1/info
```

### Multiple local model servers

Set `MODEL_ENDPOINTS` before starting the orchestrator. Separate endpoints represent separate model workers; they are not fake copies of one model.

```bash
MODEL_ENDPOINTS='local1=http://127.0.0.1:8081/v1;local2=http://127.0.0.1:8082/v1' python3 server.py
```

The existing UI tiers remain:

- Fast — up to 12 configured endpoints
- Balanced — up to 20 configured endpoints
- Smart — up to 27 configured endpoints

If fewer endpoints are actually configured, the backend reports and queries the number that really exists. It does not fabricate model counts.

## Scoring

The first implementation uses a transparent deterministic baseline score based on response presence, useful length, basic structure, and latency. This is intentionally documented as a baseline rather than pretending it is a reliable semantic judge.

A stronger judge/evaluator can be added later without changing the frontend contract.

## Verification status

The repository was inspected before adding the backend. Existing frontend behavior was preserved. The backend was added as a separate file and the README documents the actual architecture and startup path.
