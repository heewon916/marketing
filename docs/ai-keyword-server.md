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
- Container model dir: `/models/exaone-3.5-7.8b-instruct/q4_k_m`
- Container model path: `/models/exaone-3.5-7.8b-instruct/q4_k_m/model.gguf`
- Default host cache dir: `/home/ubuntu/marketing/models/keyword/exaone-3.5-7.8b-instruct/q4_k_m`
- Default source: `LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-GGUF`
- Default filename: `EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf`

### Caption Server
- Service name: `caption-server`
- Default port: `8002`
- Container model dir: `/models/exaone-4.0-32b/q4_k_m`
- Container model path: `/models/exaone-4.0-32b/q4_k_m/model.gguf`
- Default host cache dir: `/home/ubuntu/marketing/models/caption/exaone-4.0-32b/q4_k_m`
- Default source: `LGAI-EXAONE/EXAONE-4.0-32B-GGUF`
- Default filename: `EXAONE-4.0-32B-Q4_K_M.gguf`

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
2. By default, model caches are stored on absolute host paths outside `DEPLOY_DIR`.
3. Override `KEYWORD_MODEL_HOST_DIR` or `CAPTION_MODEL_HOST_DIR` only if your deployment server uses different cache locations.
4. Run the Jenkins pipeline.
5. Jenkins provisions keyword and caption GGUF artifacts if `model.gguf` is missing in either host cache directory.
6. Jenkins starts `postgres`, `redis`, `keyword-server`, and `caption-server`.
7. `fastapi` starts after both llama servers are reachable from the Docker network.

## First Deploy Checks
1. Run `docker compose config` with the deploy `.env` and confirm the keyword path resolves to `/models/exaone-3.5-7.8b-instruct/q4_k_m/model.gguf`.
2. In the same output, confirm the caption path resolves to `/models/exaone-4.0-32b/q4_k_m/model.gguf`.
3. Check Jenkins logs for:
   - `keyword-model source: LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-GGUF/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf`
   - `caption-model source: LGAI-EXAONE/EXAONE-4.0-32B-GGUF/EXAONE-4.0-32B-Q4_K_M.gguf`
4. Verify both model host cache directories contain `model.gguf` after provisioning.
5. Confirm the host cache directories are outside `/home/ubuntu/deploy/S14P31A401` so deploy cleanup does not delete the cached models.

## Runtime Behavior
- If `keyword-server` is unavailable, `process-utterance` can return `503`.
- If `caption-server` is unavailable, `FastAPI` falls back to the rule-based guide text and caption builder.
- Canonical keyword resolution remains independent of both llama servers.

## Health Checks
- Keyword server health must respond at `http://keyword-server:<KEYWORD_MODEL_SERVER_PORT>/health`.
- Caption server health must respond at `http://caption-server:<CAPTION_MODEL_SERVER_PORT>/health`.
- FastAPI health must respond at `http://fastapi:8000/ai/health`.
- Treat `docker compose config`, both llama `/health` responses, and the Jenkins source log lines above as the deployment acceptance criteria for the model switch.

## Troubleshooting
- Model file missing:
  Confirm the resolved host cache directory contains `model.gguf` for the affected role.
- Model re-downloads every deploy:
  Check whether `KEYWORD_MODEL_HOST_DIR` or `CAPTION_MODEL_HOST_DIR` was overridden to a path inside `DEPLOY_DIR`.
- Download failed:
  Check the Jenkins logs for the role-specific `repo_id`, `filename`, and target path.
- Health check failed:
  Inspect `docker compose ... logs keyword-server --tail=100` or `docker compose ... logs caption-server --tail=100`.
- Unexpected fallback text:
  Check `fastapi` logs for `caption_model_fallback` and verify `caption-server` health inside the Docker network.
