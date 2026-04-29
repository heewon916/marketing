# AI Service

This directory contains a standalone FastAPI service scaffold for AI-related APIs.

## Structure

- `app/`: FastAPI application package
- `scripts/`: local helper scripts
- `tests/`: pytest-based tests

## Quick start

```powershell
cd ai
uv sync
uv run fastapi dev app/main.py
```

## Optional keyword model runtime

The app can start without `llama-cpp-python`. In that case, the
`/ai/sessions/{session_id}/process-utterance` endpoint returns `503`
until a local keyword-extraction runtime is installed and `KEYWORD_MODEL_PATH` points
to a valid GGUF model.

`llama-cpp-python`'s default install path builds from source, which
requires MSVC/NMake on Windows. The project intentionally does not pin it
as a mandatory dependency anymore. Install a prebuilt wheel manually for
your environment when you want local keyword extraction enabled.

Examples from the official package docs:

```powershell
# CPU wheel
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# CUDA wheel example
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

After installing the runtime, point the app to a GGUF model file:

```powershell
$env:KEYWORD_MODEL_PATH = "C:\models\keyword-gguf\model.gguf"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If `KEYWORD_MODEL_PATH` is configured but the file does not exist yet,
the app now downloads a default GGUF automatically on startup or first
request. The default download target is a text-only GGUF model that
works with the official `abetlen/llama-cpp-python` runtime:

- Repo: `Qwen/Qwen2.5-7B-Instruct-GGUF`
- File: `qwen2.5-7b-instruct-q3_k_m.gguf`

The official Qwen repo stores some larger quantizations, including
`q4_k_m`, as split multi-part GGUF files. This app's downloader currently
expects a single file, so the default uses the official repo's single-file
`q3_k_m` artifact instead.

You can override either with these environment variables:

```env
KEYWORD_MODEL_HF_REPO_ID=Qwen/Qwen2.5-7B-Instruct-GGUF
KEYWORD_MODEL_HF_FILENAME=qwen2.5-7b-instruct-q3_k_m.gguf
```

The service exposes:

- `GET /api/v1/health`
- `POST /api/v1/inference`
