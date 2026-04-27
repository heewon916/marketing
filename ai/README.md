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

The service exposes:

- `GET /api/v1/health`
- `POST /api/v1/inference`
