from pathlib import Path

from scripts import bootstrap_keyword_model


def test_bootstrap_keyword_model_uses_container_model_path(monkeypatch) -> None:
    captured: dict[str, Path] = {}

    def fake_ensure_keyword_model_available(model_path: Path) -> Path:
        captured["model_path"] = model_path
        return model_path

    monkeypatch.setattr(
        bootstrap_keyword_model,
        "ensure_keyword_model_available",
        fake_ensure_keyword_model_available,
    )

    exit_code = bootstrap_keyword_model.main()

    assert exit_code == 0
    assert captured["model_path"] == Path("/models/qwen-gguf/model.gguf")
