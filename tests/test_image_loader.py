from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from x4_wallpaper_maker.core import image_loader


def test_load_source_image_registers_heif_opener_for_heic(monkeypatch, tmp_path: Path) -> None:
    source_path = tmp_path / "source.heic"
    calls: list[str] = []

    def fake_register() -> None:
        calls.append("register")

    def fake_open(_path: Path) -> Image.Image:
        return Image.new("RGB", (1200, 900), color="navy")

    monkeypatch.setattr(image_loader, "_HEIF_OPENER_REGISTERED", False)
    monkeypatch.setattr(image_loader, "_register_heif_opener", fake_register)
    monkeypatch.setattr(image_loader.Image, "open", fake_open)

    source_image, display_image, notice = image_loader.load_source_image(source_path)

    assert calls == ["register"]
    assert source_image.mode == "RGB"
    assert source_image.size == (1200, 900)
    assert display_image.size[0] <= 1600
    assert display_image.size[1] <= 1600
    assert notice is None


def test_load_source_image_reports_missing_heif_dependency(monkeypatch, tmp_path: Path) -> None:
    source_path = tmp_path / "source.heif"

    def fake_register() -> None:
        raise ImportError("missing pillow-heif")

    monkeypatch.setattr(image_loader, "_HEIF_OPENER_REGISTERED", False)
    monkeypatch.setattr(image_loader, "_register_heif_opener", fake_register)

    with pytest.raises(image_loader.SourceImageLoadError, match="HEIC support is not available yet"):
        image_loader.load_source_image(source_path)
