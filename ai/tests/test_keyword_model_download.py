from pathlib import Path

import pytest

from app.keyword_model_download import ensure_keyword_model_available


def test_ensure_keyword_model_available_returns_existing_file(tmp_path) -> None:
    model_path = tmp_path / "models" / "model.gguf"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"existing")

    resolved = ensure_keyword_model_available(model_path)

    assert resolved == model_path
    assert model_path.read_bytes() == b"existing"


def test_ensure_keyword_model_available_downloads_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_path = tmp_path / "models" / "model.gguf"
    downloaded = tmp_path / "cache" / "qwen2.5-7b-instruct-q3_k_m.gguf"
    downloaded.parent.mkdir(parents=True, exist_ok=True)
    downloaded.write_bytes(b"downloaded")

    def fake_hf_hub_download(*, repo_id: str, filename: str, repo_type: str) -> str:
        assert repo_type == "model"
        assert repo_id == "Qwen/Qwen2.5-7B-Instruct-GGUF"
        assert filename == "qwen2.5-7b-instruct-q3_k_m.gguf"
        return str(downloaded)

    monkeypatch.setattr(
        "app.keyword_model_download._hf_hub_download",
        fake_hf_hub_download,
    )

    resolved = ensure_keyword_model_available(model_path)

    assert resolved == model_path
    assert model_path.read_bytes() == b"downloaded"


def test_ensure_keyword_model_available_requires_path() -> None:
    with pytest.raises(RuntimeError, match="KEYWORD_MODEL_PATH is not configured"):
        ensure_keyword_model_available(None)
