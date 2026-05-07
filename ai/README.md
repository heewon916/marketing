# AI Service

This directory contains the standalone FastAPI service for AI-related APIs.

## Structure

- `app/`: FastAPI application package
- `scripts/`: local helper scripts
- `tests/`: pytest-based tests

## Package management

This project uses `uv` as the single source of truth for dependency management.

- Dependency definitions live in `pyproject.toml`
- Locked versions live in `uv.lock`
- Do not use `requirements.txt`

## Quick start

```powershell
cd ai
uv sync
uv run fastapi dev app/main.py
```

Run the production server locally with:

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Keyword extraction runtime

FastAPI no longer calls the keyword GGUF model directly during inference.
Instead, keyword extraction sends HTTP requests to a separately served
`llama-server` container on the same Docker Network.

- Base URL: `KEYWORD_MODEL_BASE_URL`
- Chat endpoint: `KEYWORD_MODEL_CHAT_ENDPOINT`
- Default target: `http://llama-server:8000/v1/chat/completions`

At startup, FastAPI only checks connectivity to the remote keyword server.
If the server is unavailable, the app still starts and `process-utterance`
can return `503` until the server becomes reachable.

## Keyword extraction flow

When `process-utterance` receives the first shop-owner utterance, the keyword
extraction flow now works in three steps:

1. `llama-server` classifies the utterance purpose as one of
   `메뉴 홍보`, `영업 공지`, or `일상 공유`.
2. `llama-server` extracts 1 to 3 raw keyword candidates as `keywords`.
3. FastAPI normalizes each keyword with the morphology-based nounization path
   and stores the normalized values as `draft_keywords`.

The remote model contract is therefore:

```json
{
  "purpose": "메뉴 홍보",
  "keywords": ["막걸리", "파전"]
}
```

FastAPI persists the normalized keyword state in Redis as before and also saves
the classified purpose under `debug:purpose` for internal tracing. The API
response still returns only the generated caption and guide text.

## Weather tag flow

During the first `process-utterance` call, FastAPI also evaluates reusable
weather tags from the request body's `weather` payload and stores them in the
session for later text-generation steps.

- Stored Redis fields: `weather_tag:1`, `weather_tag:2`, ...
- Current tag groups:
  - precipitation: `PRECIP_CLEAR`, `PRECIP_CLOUDY`, `PRECIP_RAIN`, `PRECIP_HEAVY_RAIN`
  - temperature: `TEMP_FREEZING`, `TEMP_COLD`, `TEMP_MILD`, `TEMP_HOT`, `TEMP_SCORCHING`
  - humidity: `HUMID_LOW`, `HUMID_HIGH`
  - special conditions: `SPECIAL_FINE_DUST`, `SPECIAL_TYPHOON`, `SPECIAL_SEASONAL_CHANGE`

Current implementation notes:

- `cloud_cover` is interpreted by string mapping such as `맑음/clear/sunny` and `흐림/cloudy/overcast/구름많음`.
- `PRECIP_SNOW` is intentionally excluded for now because the current request schema does not provide a reliable snowfall signal.
- Weather tags are internal session state only; they are not exposed in the public API response yet.

## Legacy local GGUF settings

The previous local GGUF configuration is kept in code as a legacy fallback
reference during migration, but it is no longer used by the FastAPI inference
path.

- Legacy path: `ai/models/qwen-gguf/model.gguf`
- Legacy repo: `Qwen/Qwen2.5-7B-Instruct-GGUF`
- Legacy file: `qwen2.5-7b-instruct-q3_k_m.gguf`

Container creation, Docker Compose wiring, and actual `llama-server` startup
are handled in a later task and are intentionally out of scope here.

## Linux deployment notes

Development was done on Windows, but deployment is expected to run on Linux.
Keep the following in mind when preparing the server:

- Do not copy `ai/.venv` from Windows to Linux. Create a new virtual environment on Linux and run `uv sync` there.
- Native packages such as `llama-cpp-python` are still listed for legacy compatibility, but the FastAPI service now expects a reachable remote `llama-server` for keyword extraction.
- The local GGUF model file itself is only relevant if you later restore direct local inference or use it in the separate model-serving container.
- First startup may still take time if orientation weights need to be downloaded. Plan for this in container startup and health checks.
- If you later run `llama-server` with Docker or Docker Compose, connect it to the same network as the FastAPI container and provide a stable service name such as `llama-server`.
- Verify that the server has enough disk space and memory for `tensorflow-cpu`, the orientation weights, and the separately served keyword model container.
