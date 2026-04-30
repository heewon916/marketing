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

## Keyword model runtime

Keyword extraction uses the `llama-cpp-python` runtime defined in `pyproject.toml`.
The app stores the GGUF at `ai/models/qwen-gguf/model.gguf` by default.
If the file does not exist yet, the app downloads the default GGUF automatically
on startup or on the first request.

- Repo: `Qwen/Qwen2.5-7B-Instruct-GGUF`
- File: `qwen2.5-7b-instruct-q3_k_m.gguf`

## Linux deployment notes

Development was done on Windows, but deployment is expected to run on Linux.
Keep the following in mind when preparing the server:

- Do not copy `ai/.venv` from Windows to Linux. Create a new virtual environment on Linux and run `uv sync` there.
- Native packages such as `llama-cpp-python` are platform-specific. They must be installed again on the Linux host or inside the Linux container.
- The GGUF model file itself can be reused across environments if you place it at the default app path or bake it into the image.
- First startup may take time if the keyword GGUF or orientation weights need to be downloaded. Plan for this in container startup and health checks.
- If you use Docker or Docker Compose, consider mounting persistent volumes for `models/` and `weights/` so large files are not downloaded again every time a container is recreated.
- Verify that the server has enough disk space and memory for `tensorflow-cpu`, the orientation weights, and the GGUF keyword model.
