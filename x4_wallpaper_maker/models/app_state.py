"""Application state models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AppStage(str, Enum):
    IMPORT = "import"
    CROP = "crop"
    PREVIEW = "preview"


class RenderMode(str, Enum):
    STANDARD = "standard"
    DITHERED = "dithered"
    MONO = "mono"


class ExportMode(str, Enum):
    ROOT_SLEEP = "root_sleep"
    DOT_SLEEP_FOLDER = "dot_sleep_folder"
    SLEEP_FOLDER = "sleep_folder"
    CUSTOM = "custom"


class SleepFolderVariant(str, Enum):
    DOT_SLEEP = ".sleep"
    SLEEP = "sleep"


@dataclass(slots=True)
class CropDraftState:
    scale: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    initial_scale: float = 1.0
    initial_offset_x: float = 0.0
    initial_offset_y: float = 0.0
    zoom_value: int = 0


@dataclass(slots=True)
class PreviewSettings:
    mode: RenderMode = RenderMode.STANDARD
    brightness: int = 0
    contrast: int = 0
    sharpen: bool = False


@dataclass(slots=True)
class ExportRequest:
    mode: ExportMode
    target_directory: Path | None = None
    custom_path: Path | None = None
    file_name: str | None = None
    overwrite: bool = False
    folder_variant: SleepFolderVariant = SleepFolderVariant.DOT_SLEEP


@dataclass(slots=True)
class SessionState:
    stage: AppStage = AppStage.IMPORT
    source_image_rgb: Any | None = None
    display_image_rgb: Any | None = None
    prepared_base_480x800_rgb: Any | None = None
    crop_draft: CropDraftState = field(default_factory=CropDraftState)
    confirmed_crop_box: tuple[float, float, float, float] | None = None
    preview_settings: PreviewSettings = field(default_factory=PreviewSettings)
    export_draft: ExportRequest | None = None
    current_preview_image: Any | None = None
    import_notice: str | None = None
    render_revision: int = 0
