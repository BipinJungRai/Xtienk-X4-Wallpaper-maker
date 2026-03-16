"""High-level session orchestration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PIL import Image

from x4_wallpaper_maker.core import crop_engine, export_engine, image_loader, render_engine
from x4_wallpaper_maker.core.privacy_manager import PrivacyManager
from x4_wallpaper_maker.models.app_state import AppStage, CropDraftState, ExportRequest, PreviewSettings, RenderMode, SessionState
from x4_wallpaper_maker.utils.constants import DEFAULT_EXPORT_FILENAME


def _pil_to_qimage(image: Image.Image):
    try:
        from PySide6.QtGui import QImage
    except ImportError:
        return None

    if image.mode == "L":
        payload = image.tobytes("raw", "L")
        qimage = QImage(payload, image.width, image.height, image.width, QImage.Format.Format_Grayscale8)
    else:
        rgb = image.convert("RGB")
        payload = rgb.tobytes("raw", "RGB")
        qimage = QImage(payload, rgb.width, rgb.height, rgb.width * 3, QImage.Format.Format_RGB888)
    return qimage.copy()


class SessionManager:
    def __init__(self, privacy_manager: PrivacyManager | None = None) -> None:
        self.privacy_manager = privacy_manager or PrivacyManager()
        self.logger = self.privacy_manager.logger
        self.state = SessionState()

    def import_source(self, path: str | Path) -> SessionState:
        self.clear_session()
        source_path = Path(path)
        source_image, display_image, notice = image_loader.load_source_image(path)
        self.state.source_image_rgb = source_image
        self.state.display_image_rgb = display_image
        self.state.source_image_stem = source_path.stem or Path(DEFAULT_EXPORT_FILENAME).stem
        self.state.stage = AppStage.CROP
        self.state.crop_draft = CropDraftState()
        self.state.preview_settings = PreviewSettings(mode=RenderMode.STANDARD)
        self.state.import_notice = notice
        self.state.render_revision += 1
        self.logger.info("event=import status=ok")
        return self.state

    def fit_crop(self, canvas_size: tuple[int, int]) -> CropDraftState:
        if self.state.display_image_rgb is None:
            raise ValueError("No image loaded.")
        self.state.crop_draft = crop_engine.fit_crop_state(self.state.display_image_rgb.size, canvas_size)
        return self.state.crop_draft

    def reset_crop(self, canvas_size: tuple[int, int]) -> CropDraftState:
        return self.fit_crop(canvas_size)

    def rotate_source(self, *, clockwise: bool) -> SessionState:
        if self.state.source_image_rgb is None or self.state.display_image_rgb is None:
            raise ValueError("No image loaded.")

        transform = Image.Transpose.ROTATE_270 if clockwise else Image.Transpose.ROTATE_90
        self.state.source_image_rgb = self.state.source_image_rgb.transpose(transform)
        self.state.display_image_rgb = self.state.display_image_rgb.transpose(transform)
        self.state.crop_draft = CropDraftState()
        self.state.confirmed_crop_box = None
        self.state.prepared_base_480x800_rgb = None
        self.state.current_preview_image = None
        self.state.stage = AppStage.CROP
        self.state.render_revision += 1
        return self.state

    def update_crop_draft(
        self,
        *,
        canvas_size: tuple[int, int],
        scale: float | None = None,
        offset_x: float | None = None,
        offset_y: float | None = None,
        zoom_value: int | None = None,
    ) -> CropDraftState:
        if self.state.display_image_rgb is None:
            raise ValueError("No image loaded.")

        current = self.state.crop_draft
        if zoom_value is not None:
            self.state.crop_draft = crop_engine.zoom_crop_state(
                self.state.display_image_rgb.size,
                canvas_size,
                current,
                zoom_value,
            )
            return self.state.crop_draft

        updated = replace(
            current,
            scale=current.scale if scale is None else scale,
            offset_x=current.offset_x if offset_x is None else offset_x,
            offset_y=current.offset_y if offset_y is None else offset_y,
        )
        self.state.crop_draft = crop_engine.clamp_crop_state(
            self.state.display_image_rgb.size,
            canvas_size,
            updated,
        )
        return self.state.crop_draft

    def confirm_crop(self, canvas_size: tuple[int, int]) -> SessionState:
        if self.state.source_image_rgb is None or self.state.display_image_rgb is None:
            raise ValueError("No image loaded.")

        if self.state.crop_draft.scale <= 0:
            self.fit_crop(canvas_size)

        normalized_box = crop_engine.resolve_crop_box(
            self.state.display_image_rgb.size,
            canvas_size,
            self.state.crop_draft,
        )
        self.state.confirmed_crop_box = normalized_box
        self.state.prepared_base_480x800_rgb = render_engine.prepare_base_image(self.state.source_image_rgb, normalized_box)
        self.state.stage = AppStage.PREVIEW
        self.state.render_revision += 1
        self._refresh_preview_image()
        return self.state

    def update_preview_settings(
        self,
        *,
        mode: RenderMode | None = None,
        brightness: int | None = None,
        contrast: int | None = None,
        sharpen: bool | None = None,
    ) -> PreviewSettings:
        self.state.preview_settings = replace(
            self.state.preview_settings,
            mode=self.state.preview_settings.mode if mode is None else mode,
            brightness=self.state.preview_settings.brightness if brightness is None else brightness,
            contrast=self.state.preview_settings.contrast if contrast is None else contrast,
            sharpen=self.state.preview_settings.sharpen if sharpen is None else sharpen,
        )
        self._refresh_preview_image()
        return self.state.preview_settings

    def export(self, request: ExportRequest) -> Path:
        if self.state.prepared_base_480x800_rgb is None:
            raise ValueError("Nothing is ready to export.")
        rendered = render_engine.render_export_bitmap(self.state.prepared_base_480x800_rgb, self.state.preview_settings)
        target_path = export_engine.export_bmp(rendered, request)
        self.state.export_draft = request
        self.logger.info("event=export status=ok")
        return target_path

    def clear_session(self) -> SessionState:
        self.privacy_manager.clear_session(self.state)
        self.state = SessionState()
        return self.state

    def shutdown_cleanup(self) -> None:
        self.privacy_manager.shutdown_cleanup(self.state)
        self.state = SessionState()

    def default_export_path(self, downloads_dir: Path | None = None) -> Path:
        export_root = downloads_dir or (Path.home() / "Downloads")
        export_name = export_engine.normalize_export_filename(self.state.source_image_stem)
        return export_root / export_name

    def _refresh_preview_image(self) -> None:
        if self.state.prepared_base_480x800_rgb is None:
            self.state.current_preview_image = None
            return
        rendered = render_engine.render_preview(self.state.prepared_base_480x800_rgb, self.state.preview_settings)
        self.state.current_preview_image = _pil_to_qimage(rendered)
