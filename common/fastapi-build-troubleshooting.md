# FastAPI Remote Build Troubleshooting

Use this guide when the deployment server fails while building the `fastapi`
service image, especially if the failure happens during `uv sync` or while
extracting a large wheel such as `torch`.

## Quick Start

From the deployment repository root on the Ubuntu server:

```bash
bash common/diagnose-fastapi-build.sh
```

To collect the baseline snapshots and then re-run only the FastAPI build:

```bash
bash common/diagnose-fastapi-build.sh --rebuild-fastapi
```

The script assumes the same defaults used by deployment:

- compose project: `marketing`
- compose file: `compose.yaml`
- env file: `.env`

Override them if needed:

```bash
PROJECT_NAME=marketing-staging bash common/diagnose-fastapi-build.sh
```

## What The Script Checks

- `df -h` for filesystem capacity.
- `df -i` for inode exhaustion.
- `docker system df -v` for image, container, volume, and build cache usage.
- `du -sh /var/lib/docker` and `du -sh /var/lib/docker/overlay2` for Docker's
  actual storage footprint.
- `du -sh /var/lib/jenkins` and `du -sh /tmp` for common deployment-side
  storage pressure sources.
- `docker images`, `docker ps -a`, and `docker builder ls` for accumulated
  artifacts and builder state.
- Optional `docker compose ... build fastapi` replay to observe whether storage
  drops sharply during the rebuild.

## How To Interpret Results

### Classify as `server storage issue`

Use this label if any of the following is true:

- the root filesystem is nearly full
- `/var/lib/docker` or its backing partition is nearly full
- the rebuild fails again while free space drops during `uv sync`

This is the most likely direct cause for the current failure because the build
log already shows:

```text
Failed to extract archive ... torch ... No space left on device (os error 28)
```

### Classify as `server artifact accumulation`

Use this label if Docker reports large reclaimable data:

- dangling images
- stopped containers
- oversized build cache
- old layers left in `overlay2`

This means the server likely can build in principle, but previous deployment
artifacts consumed the headroom needed for the FastAPI image.

### Classify as `Dockerfile/build-structure issue`

Use this label if server headroom looks reasonable but the AI image still grows
too aggressively during the build.

Current repository-specific signals:

- [ai/Dockerfile](../ai/Dockerfile) runs `uv sync`
  twice.
- The Dockerfile sets `UV_LINK_MODE=copy`, which prefers copying files into the
  environment instead of linking them.
- Large dependencies are installed before the project sources are copied, then
  installed again after `COPY . .`.

These choices are good candidates for space amplification during image build.

### Classify as `dependency footprint issue`

Use this label if the server is otherwise healthy but the dependency set itself
is too large for the current host budget.

High-priority packages from [ai/pyproject.toml](../ai/pyproject.toml)
and [ai/uv.lock](../ai/uv.lock):

- `torch`
- `opencv-python-headless`
- `onnxruntime`
- `kiwipiepy`
- `kiwipiepy-model`
- `matplotlib`
- `transformers`

`torch` is not merely optional in the current codebase. It is imported by:

- [ai/app/services/canonical_keyword_resolver.py](../ai/app/services/canonical_keyword_resolver.py)
- [ai/app/services/final_edit_upscaler.py](../ai/app/services/final_edit_upscaler.py)

So the first question is not "can we remove it immediately," but "is the
current build host sized for it, and is the build layout making it worse?"

## Notes

- The `Docker Compose requires buildx plugin to be installed` warning should be
  treated as a secondary efficiency concern, not the primary failure cause.
- Share the script output together with the Jenkins failure log when comparing
  root-cause hypotheses.
