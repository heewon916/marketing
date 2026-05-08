# AI Llama Server Deployment

## Overview
- The AI stack runs two dedicated `llama.cpp` servers.
- `keyword-server` serves the keyword extraction model.
- `caption-server` serves the guide text and caption generation model.
- Jenkins provisions both GGUF files before `docker compose up`.

## Server Layout

### Keyword Server
- Service name: `keyword-server`
- Default port: `8001`
- Container model dir: `/models/qwen2-1.5b-instruct/q3_k_m`
- Container model path: `/models/qwen2-1.5b-instruct/q3_k_m/model.gguf`
- Default host cache dir: `./.models/keyword/qwen2-1.5b-instruct/q3_k_m`
- Default source: `Qwen/Qwen2-1.5B-Instruct-GGUF`
- Default filename: `qwen2-1.5b-instruct-q3_k_m.gguf`

### Caption Server
- Service name: `caption-server`
- Default port: `8002`
- Container model dir: `/models/qwen2.5-7b-instruct/q3_k_m`
- Container model path: `/models/qwen2.5-7b-instruct/q3_k_m/model.gguf`
- Default host cache dir: `./.models/caption/qwen2.5-7b-instruct/q3_k_m`
- Default source: `Qwen/Qwen2.5-7B-Instruct-GGUF`
- Default filename: `qwen2.5-7b-instruct-q3_k_m.gguf`

## FastAPI Runtime Env

### Keyword Model Client
- `KEYWORD_MODEL_BASE_URL`
- `KEYWORD_MODEL_CHAT_ENDPOINT`
- `KEYWORD_MODEL_HEALTH_ENDPOINT`
- `KEYWORD_MODEL_API_KEY`
- `KEYWORD_MODEL_TIMEOUT_SECONDS`
- `KEYWORD_MODEL_MAX_TOKENS`
- `KEYWORD_MODEL_TEMPERATURE`
- `KEYWORD_MODEL_TOP_P`
- `KEYWORD_MODEL_ENABLED`

### Caption Model Client
- `CAPTION_MODEL_BASE_URL`
- `CAPTION_MODEL_CHAT_ENDPOINT`
- `CAPTION_MODEL_HEALTH_ENDPOINT`
- `CAPTION_MODEL_API_KEY`
- `CAPTION_MODEL_TIMEOUT_SECONDS`
- `CAPTION_MODEL_MAX_TOKENS`
- `CAPTION_MODEL_TEMPERATURE`
- `CAPTION_MODEL_TOP_P`
- `CAPTION_MODEL_ENABLED`

## Deployment Env

### Keyword Server
- `KEYWORD_MODEL_HOST_DIR`
- `KEYWORD_MODEL_HF_REPO_ID`
- `KEYWORD_MODEL_HF_FILENAME`
- `KEYWORD_MODEL_SERVER_PORT`
- `KEYWORD_MODEL_CTX_SIZE`
- `KEYWORD_MODEL_GPU_LAYERS`

### Caption Server
- `CAPTION_MODEL_HOST_DIR`
- `CAPTION_MODEL_HF_REPO_ID`
- `CAPTION_MODEL_HF_FILENAME`
- `CAPTION_MODEL_SERVER_PORT`
- `CAPTION_MODEL_CTX_SIZE`
- `CAPTION_MODEL_GPU_LAYERS`

## First Deploy
1. Fill out `.env`.
2. Set model overrides only if the defaults are not suitable.
3. Run the Jenkins pipeline.
4. Jenkins provisions keyword and caption GGUF artifacts if `model.gguf` is missing in either host cache directory.
5. Jenkins starts `postgres`, `redis`, `keyword-server`, and `caption-server`.
6. `fastapi` starts after both llama servers are reachable from the Docker network.

## Runtime Behavior
- If `keyword-server` is unavailable, `process-utterance` can return `503`.
- If `caption-server` is unavailable, `FastAPI` falls back to the rule-based guide text and caption builder.
- Canonical keyword resolution remains independent of both llama servers.

## Health Checks
- Keyword server health must respond at `http://keyword-server:<KEYWORD_MODEL_SERVER_PORT>/health`.
- Caption server health must respond at `http://caption-server:<CAPTION_MODEL_SERVER_PORT>/health`.
- FastAPI health must respond at `http://fastapi:8000/ai/health`.

## Troubleshooting
- Model file missing:
  Confirm the resolved host cache directory contains `model.gguf` for the affected role.
- Download failed:
  Check the Jenkins logs for the role-specific `repo_id`, `filename`, and target path.
- Health check failed:
  Inspect `docker compose ... logs keyword-server --tail=100` or `docker compose ... logs caption-server --tail=100`.
- Unexpected fallback text:
  Check `fastapi` logs for `caption_model_fallback` and verify `caption-server` health inside the Docker network.
