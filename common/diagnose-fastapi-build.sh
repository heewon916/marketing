#!/usr/bin/env bash

set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-marketing}"
COMPOSE_FILE="${COMPOSE_FILE:-compose.yaml}"
ENV_FILE="${ENV_FILE:-.env}"
REBUILD_FASTAPI=0

usage() {
  cat <<'EOF'
Usage:
  bash common/diagnose-fastapi-build.sh [--rebuild-fastapi] [--project-name NAME] [--compose-file PATH] [--env-file PATH]

Options:
  --rebuild-fastapi       Re-run `docker compose build fastapi` after the initial snapshots.
  --project-name NAME     Override the compose project name. Default: marketing
  --compose-file PATH     Override the compose file path. Default: compose.yaml
  --env-file PATH         Override the env file path. Default: .env
  -h, --help              Show this help message.

Examples:
  bash common/diagnose-fastapi-build.sh
  bash common/diagnose-fastapi-build.sh --rebuild-fastapi
  PROJECT_NAME=marketing-staging bash common/diagnose-fastapi-build.sh
EOF
}

while (($# > 0)); do
  case "$1" in
    --rebuild-fastapi)
      REBUILD_FASTAPI=1
      shift
      ;;
    --project-name)
      PROJECT_NAME="$2"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

if [[ $EUID -eq 0 ]]; then
  SUDO=()
elif command -v sudo >/dev/null 2>&1; then
  SUDO=(sudo)
else
  SUDO=()
fi

section() {
  printf '\n===== %s =====\n' "$1"
}

run_or_warn() {
  if ! "$@"; then
    echo "[warn] command failed: $*" >&2
  fi
}

run_disk_checks() {
  section "Disk Usage (df -h)"
  df -h

  section "Disk Inodes (df -i)"
  df -i

  section "Docker Storage Summary (docker system df -v)"
  run_or_warn docker system df -v

  section "Docker Directory Size"
  run_or_warn "${SUDO[@]}" du -sh /var/lib/docker
  run_or_warn "${SUDO[@]}" du -sh /var/lib/docker/overlay2

  section "Jenkins and Tmp Directory Size"
  run_or_warn "${SUDO[@]}" du -sh /var/lib/jenkins
  run_or_warn "${SUDO[@]}" du -sh /tmp
}

run_docker_inventory() {
  section "Docker Images"
  run_or_warn docker images

  section "Docker Containers"
  run_or_warn docker ps -a

  section "Docker Builder"
  run_or_warn docker builder ls
}

print_interpretation_guide() {
  section "Interpretation Guide"
  cat <<'EOF'
- If the root filesystem or `/var/lib/docker` is close to full, treat server storage pressure as the primary cause.
- If any filesystem shows inode exhaustion in `df -i`, treat it as a file-count limit rather than a byte-capacity limit.
- If `docker system df -v` shows large reclaimable cache, dangling images, or stopped containers, classify the issue as accumulated Docker artifacts on the server.
- If the rebuild fails again during `uv sync` while unpacking `torch`, and disk usage spikes at the same time, classify the direct failure as storage exhaustion triggered by heavy AI dependencies.
- If disk headroom looks healthy but the build still expands sharply during the two `uv sync` steps, keep `ai/Dockerfile` and dependency layout as a secondary structural cause.
- The `Docker Compose requires buildx plugin to be installed` warning is a secondary efficiency signal, not the primary failure cause.
EOF
}

run_fastapi_rebuild() {
  local status

  section "FastAPI Rebuild Command"
  echo "docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} --env-file ${ENV_FILE} build fastapi"

  set +e
  docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build fastapi
  status=$?
  set -e

  section "Post-Rebuild Disk Usage (df -h)"
  df -h

  section "Post-Rebuild Docker Storage Summary (docker system df -v)"
  run_or_warn docker system df -v

  if [[ $status -ne 0 ]]; then
    echo "[result] fastapi rebuild failed with exit code ${status}"
  else
    echo "[result] fastapi rebuild completed successfully"
  fi

  return "$status"
}

section "Diagnostic Context"
echo "timestamp: $(date -Is)"
echo "host: $(hostname)"
echo "user: $(whoami)"
echo "pwd: $(pwd)"
echo "project_name: ${PROJECT_NAME}"
echo "compose_file: ${COMPOSE_FILE}"
echo "env_file: ${ENV_FILE}"

run_disk_checks
run_docker_inventory
print_interpretation_guide

if [[ $REBUILD_FASTAPI -eq 1 ]]; then
  run_fastapi_rebuild
fi
