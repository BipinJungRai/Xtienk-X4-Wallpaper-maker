from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from x4_wallpaper_maker.core.export_engine import build_target_path, export_bmp
from x4_wallpaper_maker.models.app_state import ExportMode, ExportRequest, SleepFolderVariant


def _bitmap() -> Image.Image:
    return Image.new("L", (480, 800), color=200)


def test_root_sleep_export_writes_sleep_bmp(tmp_path: Path) -> None:
    request = ExportRequest(mode=ExportMode.ROOT_SLEEP, target_directory=tmp_path)
    target = export_bmp(_bitmap(), request)

    assert target.name == "sleep.bmp"
    with Image.open(target) as reopened:
        assert reopened.size == (480, 800)
        assert reopened.format == "BMP"


def test_dot_sleep_export_writes_into_hidden_sleep_directory(tmp_path: Path) -> None:
    request = ExportRequest(
        mode=ExportMode.DOT_SLEEP_FOLDER,
        target_directory=tmp_path,
        file_name="custom-name.bmp",
        folder_variant=SleepFolderVariant.DOT_SLEEP,
    )
    target = export_bmp(_bitmap(), request)
    assert target == tmp_path / ".sleep" / "custom-name.bmp"


def test_sleep_folder_export_writes_into_fallback_directory(tmp_path: Path) -> None:
    request = ExportRequest(
        mode=ExportMode.SLEEP_FOLDER,
        target_directory=tmp_path,
        file_name="fallback-name.bmp",
        folder_variant=SleepFolderVariant.SLEEP,
    )
    target = export_bmp(_bitmap(), request)
    assert target == tmp_path / "sleep" / "fallback-name.bmp"


def test_custom_export_appends_bmp_suffix_when_missing(tmp_path: Path) -> None:
    request = ExportRequest(mode=ExportMode.CUSTOM, custom_path=tmp_path / "named-output")
    assert build_target_path(request) == tmp_path / "named-output.bmp"


def test_export_refuses_to_overwrite_without_confirmation(tmp_path: Path) -> None:
    target = tmp_path / "sleep.bmp"
    _bitmap().save(target, format="BMP")
    request = ExportRequest(mode=ExportMode.ROOT_SLEEP, target_directory=tmp_path, overwrite=False)
    with pytest.raises(FileExistsError):
        export_bmp(_bitmap(), request)

