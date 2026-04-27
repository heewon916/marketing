FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

COPY ai/pyproject.toml /app/pyproject.toml
RUN uv sync --no-dev

COPY ai/app /app/app

ENV PATH="/app/.venv/Scripts:/app/.venv/bin:$PATH"

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
