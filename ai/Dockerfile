FROM python:3.12-slim

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev
RUN uv run python -c "import cv2; print('cv2 ok:', cv2.__version__)"

# 배포 후 docker inspect로 실제 배포된 Git 커밋을 확인하기 위한 이미지 메타데이터
ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
