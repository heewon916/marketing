from pathlib import Path

from app.keyword_model_download import ensure_keyword_model_available

CONTAINER_KEYWORD_MODEL_PATH = Path(
    "/models/qwen2.5-7b-instruct/q3_k_m/model.gguf"
)


def main() -> int:
    resolved = ensure_keyword_model_available(CONTAINER_KEYWORD_MODEL_PATH)
    print(f"Keyword model ready at {resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
