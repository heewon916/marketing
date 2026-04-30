from pathlib import Path

import pytest

from app import keyword_model_download
from app.core import config
from app.core.config import settings
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


def test_ensure_keyword_model_available_uses_default_path_when_not_provided(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    downloaded = tmp_path / "cache" / "qwen2.5-7b-instruct-q3_k_m.gguf"
    default_model_path = tmp_path / "models" / "qwen-gguf" / "model.gguf"
    downloaded.parent.mkdir(parents=True, exist_ok=True)
    downloaded.write_bytes(b"default")

    def fake_hf_hub_download(*, repo_id: str, filename: str, repo_type: str) -> str:
        assert repo_id == settings.KEYWORD_MODEL_HF_REPO_ID
        assert filename == settings.KEYWORD_MODEL_HF_FILENAME
        assert repo_type == "model"
        return str(downloaded)

    monkeypatch.setattr(keyword_model_download, "_hf_hub_download", fake_hf_hub_download)
    monkeypatch.setattr(config, "DEFAULT_KEYWORD_MODEL_PATH", default_model_path)

    resolved = ensure_keyword_model_available()

    assert resolved == default_model_path
    assert default_model_path.read_bytes() == b"default"
