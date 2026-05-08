# AI Keyword Server Deployment

## Overview
- `keyword-server` serves a single GGUF file through `ghcr.io/ggml-org/llama.cpp:server`.
- The serving path inside the container is fixed to `/models/qwen2.5-7b-instruct/q3_k_m/model.gguf`.
- The default host cache path is `./.models/keyword/qwen2.5-7b-instruct/q3_k_m/model.gguf`.
- Jenkins provisions the GGUF file before `docker compose up -d postgres redis keyword-server`.

## Model Path Contract
- Container mount target: `/models/qwen2.5-7b-instruct/q3_k_m`
- Container model file: `/models/qwen2.5-7b-instruct/q3_k_m/model.gguf`
- Default host cache directory: `./.models/keyword/qwen2.5-7b-instruct/q3_k_m`
- Default host model file: `./.models/keyword/qwen2.5-7b-instruct/q3_k_m/model.gguf`

## Env Keys
Required:
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `S3_BUCKET_NAME`
- `S3_REGION`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `CLOUDFRONT_DOMAIN`
- `VITE_KAKAO_MAP_KEY`
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_MEASUREMENT_ID`
- `VITE_FIREBASE_APP_ID`
- `VITE_FIREBASE_VAPID_KEY`
- `VITE_API_BACKEND_URL`
- `JWT_SECRET`
- `OAUTH_REDIRECT_URI`
- `FRONTEND_URL`
- `INSTAGRAM_CLIENT_ID`
- `INSTAGRAM_CLIENT_SECRET`
- `FIREBASE_ENABLED`

Optional keyword-server keys:
- `KEYWORD_MODEL_HOST_DIR`
Default: `./.models/keyword/qwen2.5-7b-instruct/q3_k_m`
- `KEYWORD_MODEL_HF_REPO_ID`
Default: `Qwen/Qwen2.5-7B-Instruct-GGUF`
- `KEYWORD_MODEL_HF_FILENAME`
Default: `qwen2.5-7b-instruct-q3_k_m.gguf`
- `KEYWORD_MODEL_CTX_SIZE`
Default: `2048`
- `KEYWORD_MODEL_GPU_LAYERS`
Default: `0` in `compose.yaml`
- `KEYWORD_MODEL_BASE_URL`
Default: `http://keyword-server:8001`
- `KEYWORD_MODEL_CHAT_ENDPOINT`
Default: `/v1/chat/completions`
- `KEYWORD_MODEL_TIMEOUT_SECONDS`
Default: `30.0`

## First Deploy
1. Fill out `.env`. `KEYWORD_MODEL_HOST_DIR` can be omitted if the default cache path is acceptable.
2. Run the Jenkins pipeline.
3. During `Provision Keyword Model`, Jenkins resolves the host cache directory, creates it, and downloads the configured GGUF file if `model.gguf` is missing.
4. Jenkins then starts `postgres`, `redis`, and `keyword-server`.
5. The health check passes only when `http://keyword-server:8001/health` returns success from inside the Docker network.

## Redeploy
1. Keep the existing host cache directory intact.
2. Re-run the Jenkins pipeline.
3. If `./.models/keyword/qwen2.5-7b-instruct/q3_k_m/model.gguf` already exists, Jenkins skips the download step.
4. `docker compose up` reuses the cached file through the existing bind mount.

## Troubleshooting
- Model file missing:
Check whether `Provision Keyword Model` created the resolved host directory and whether `model.gguf` exists at the final path.
- Download failed:
Check the Jenkins log for the exact `repo_id`, `filename`, and target path printed by the provisioning stage. Then verify outbound access to Hugging Face and available disk space on the deploy host.
- Health check failed:
Inspect `docker compose ... logs keyword-server --tail=100` and confirm that the bind mount contains `/models/qwen2.5-7b-instruct/q3_k_m/model.gguf` inside the container.
- Custom host directory behaves unexpectedly:
If `KEYWORD_MODEL_HOST_DIR` is relative, Jenkins resolves it relative to `${DEPLOY_DIR}` before mounting it into Docker Compose.
