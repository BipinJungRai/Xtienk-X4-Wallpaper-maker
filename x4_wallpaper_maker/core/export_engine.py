"""BMP export helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from x4_wallpaper_maker.models.app_state import ExportMode, ExportRequest, SleepFolderVariant
from x4_wallpaper_maker.utils.constants import (
    DEFAULT_EXPORT_FILENAME,
    DOT_SLEEP_DIRECTORY,
    ROOT_SLEEP_FILENAME,
    SLEEP_DIRECTORY,
)


def _normalize_filename(file_name: str | None) -> str:
    candidate = (file_name or DEFAULT_EXPORT_FILENAME).strip()
    if not candidate:
        candidate = DEFAULT_EXPORT_FILENAME
    path = Path(candidate)
    if path.suffix and path.suffix.lower() != ".bmp":
        raise ValueError("Export filename must use the .bmp extension.")
    return path.name if path.suffix else f"{path.name}.bmp"


def build_target_path(request: ExportRequest) -> Path:
    if request.mode == ExportMode.CUSTOM:
        if request.custom_path is None:
            raise ValueError("Custom exports require a file path.")
        custom_path = request.custom_path
        if custom_path.suffix and custom_path.suffix.lower() != ".bmp":
            raise ValueError("Custom export path must use the .bmp extension.")
        return custom_path if custom_path.suffix else custom_path.with_suffix(".bmp")

    if request.target_directory is None:
        raise ValueError("Folder-based exports require a target directory.")

    if request.mode == ExportMode.ROOT_SLEEP:
        return request.target_directory / ROOT_SLEEP_FILENAME

    folder_name = DOT_SLEEP_DIRECTORY if request.folder_variant == SleepFolderVariant.DOT_SLEEP else SLEEP_DIRECTORY
    export_dir = request.target_directory / folder_name
    return export_dir / _normalize_filename(request.file_name)


def export_bmp(image: Image.Image, request: ExportRequest) -> Path:
    target_path = build_target_path(request)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and not request.overwrite:
        raise FileExistsError("Refusing to overwrite an existing file without confirmation.")
    image.save(target_path, format="BMP")
    return target_path

