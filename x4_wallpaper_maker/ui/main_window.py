"""Main window for X4 Wallpaper Maker."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from x4_wallpaper_maker.core.image_loader import SourceImageLoadError
from x4_wallpaper_maker.core.session_manager import SessionManager
from x4_wallpaper_maker.core.privacy_manager import PrivacyManager
from x4_wallpaper_maker.models.app_state import AppStage, ExportMode, ExportRequest, PreviewSettings
from x4_wallpaper_maker.ui.crop_view import CropView
from x4_wallpaper_maker.ui.import_view import ImportView
from x4_wallpaper_maker.ui.preview_view import PreviewView
from x4_wallpaper_maker.utils.constants import (
    APP_TITLE,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    PALETTE,
    PREVIEW_DEBOUNCE_MS,
    SUPPORTED_INPUT_EXTENSIONS,
    SUPPORTED_INPUT_NAME_FILTER,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from x4_wallpaper_maker.utils.file_dialogs import select_import_file

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self, privacy_manager: PrivacyManager | None = None, parent=None) -> None:
        super().__init__(parent)
        self.privacy_manager = privacy_manager or PrivacyManager()
        self.session = SessionManager(self.privacy_manager)
        self._pending_preview_settings = PreviewSettings()
        self._shutdown_complete = False

        self.setWindowTitle(APP_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self._apply_style()

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(PREVIEW_DEBOUNCE_MS)
        self.preview_timer.timeout.connect(self._commit_preview_settings)

        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        top_bar = QFrame(self)
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 16, 20, 16)
        top_layout.setSpacing(12)

        title_label = QLabel(APP_TITLE)
        title_label.setObjectName("appTitle")
        top_layout.addWidget(title_label)
        top_layout.addStretch(1)

        privacy_badge = QLabel("Local only")
        privacy_badge.setObjectName("privacyBadge")
        top_layout.addWidget(privacy_badge)

        self.clear_button = QPushButton("Clear session")
        self.clear_button.clicked.connect(self._clear_session)
        top_layout.addWidget(self.clear_button)

        root_layout.addWidget(top_bar)

        self.stack = QStackedWidget(self)
        root_layout.addWidget(self.stack, stretch=1)

        self.import_view = ImportView(self)
        self.crop_view = CropView(self)
        self.preview_view = PreviewView(self)
        self.stack.addWidget(self.import_view)
        self.stack.addWidget(self.crop_view)
        self.stack.addWidget(self.preview_view)

        self.import_view.selectRequested.connect(self._select_import_image)
        self.import_view.fileDropped.connect(self._import_image)

        self.crop_view.fitRequested.connect(self._fit_crop)
        self.crop_view.resetRequested.connect(self._reset_crop)
        self.crop_view.rotateLeftRequested.connect(self._rotate_left)
        self.crop_view.rotateRightRequested.connect(self._rotate_right)
        self.crop_view.zoomChanged.connect(self._update_crop_zoom)
        self.crop_view.draftEdited.connect(self._sync_crop_draft)
        self.crop_view.continueRequested.connect(self._continue_to_preview)
        self.crop_view.backRequested.connect(self._clear_session)

        self.preview_view.settingsEdited.connect(self._schedule_preview_update)
        self.preview_view.backRequested.connect(self._back_to_crop)
        self.preview_view.exportRequested.connect(self._show_export_dialog)

        clear_action = QAction("Clear session", self)
        clear_action.triggered.connect(self._clear_session)
        self.addAction(clear_action)

        self._show_stage(AppStage.IMPORT)
        self._update_controls()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {PALETTE["window"]};
                color: {PALETTE["text"]};
            }}
            #topBar {{
                background: {PALETTE["panel"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 18px;
            }}
            #appTitle {{
                font-size: 24px;
                font-weight: 700;
            }}
            #privacyBadge {{
                padding: 6px 12px;
                border-radius: 999px;
                background: {PALETTE["panel_alt"]};
                color: {PALETTE["accent_dark"]};
                font-weight: 600;
            }}
            #dropZone, #sidePanel {{
                background: {PALETTE["panel"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 28px;
            }}
            #heroTitle {{
                font-size: 34px;
                font-weight: 700;
            }}
            #heroSubtitle {{
                color: {PALETTE["muted"]};
                font-size: 16px;
            }}
            #helperLabel {{
                color: {PALETTE["muted"]};
            }}
            #sectionTitle {{
                font-size: 24px;
                font-weight: 700;
            }}
            #fieldLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {PALETTE["muted"]};
            }}
            #modeButton {{
                min-height: 34px;
                padding: 8px 12px;
            }}
            QPushButton {{
                background: {PALETTE["panel_alt"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 12px;
                padding: 10px 14px;
            }}
            QPushButton:hover {{
                border-color: {PALETTE["accent"]};
            }}
            QPushButton:checked, #primaryButton {{
                background: {PALETTE["accent"]};
                color: #ffffff;
                border-color: {PALETTE["accent_dark"]};
            }}
            QSlider::groove:horizontal {{
                border-radius: 999px;
                background: {PALETTE["panel_alt"]};
                height: 6px;
            }}
            QSlider::handle:horizontal {{
                background: {PALETTE["accent_dark"]};
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            """
        )

    def _select_import_image(self) -> None:
        selected = select_import_file(self, "Select Image", SUPPORTED_INPUT_NAME_FILTER)
        if selected is not None:
            self._import_image(str(selected))

    def _import_image(self, path: str) -> None:
        if Path(path).suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
            self._show_generic_error("That file type is not supported.")
            return
        try:
            state = self.session.import_source(path)
        except SourceImageLoadError as exc:
            self.privacy_manager.logger.error("event=import status=failed code=import_error")
            self._show_generic_error(str(exc))
            return
        except Exception:
            self.privacy_manager.logger.error("event=import status=failed code=import_error")
            self._show_generic_error("Could not open that image.")
            return

        self.crop_view.set_display_image(state.display_image_rgb, state.import_notice)
        self._show_stage(AppStage.CROP)
        QTimer.singleShot(0, self._fit_crop)
        self._update_controls()

    def _fit_crop(self) -> None:
        if self.session.state.display_image_rgb is None:
            return
        try:
            draft = self.session.fit_crop(self.crop_view.canvas_size())
        except Exception:
            return
        self.crop_view.set_draft_state(draft)

    def _reset_crop(self) -> None:
        if self.session.state.display_image_rgb is None:
            return
        draft = self.session.reset_crop(self.crop_view.canvas_size())
        self.crop_view.set_draft_state(draft)

    def _rotate_left(self) -> None:
        self._rotate_crop_image(clockwise=False)

    def _rotate_right(self) -> None:
        self._rotate_crop_image(clockwise=True)

    def _rotate_crop_image(self, *, clockwise: bool) -> None:
        if self.session.state.display_image_rgb is None:
            return
        try:
            state = self.session.rotate_source(clockwise=clockwise)
        except Exception:
            self.privacy_manager.logger.error("event=rotate status=failed code=rotate_error")
            self._show_generic_error("Could not rotate that image.")
            return
        self.crop_view.set_display_image(state.display_image_rgb, state.import_notice)

    def _update_crop_zoom(self, zoom_value: int) -> None:
        if self.session.state.display_image_rgb is None:
            return
        draft = self.session.update_crop_draft(canvas_size=self.crop_view.canvas_size(), zoom_value=zoom_value)
        self.crop_view.set_draft_state(draft)

    def _sync_crop_draft(self, draft) -> None:
        if self.session.state.display_image_rgb is None:
            return
        synced = self.session.update_crop_draft(
            canvas_size=self.crop_view.canvas_size(),
            scale=draft.scale,
            offset_x=draft.offset_x,
            offset_y=draft.offset_y,
        )
        self.crop_view.set_draft_state(synced)

    def _continue_to_preview(self) -> None:
        try:
            state = self.session.confirm_crop(self.crop_view.canvas_size())
        except Exception:
            self.privacy_manager.logger.error("event=preview_prepare status=failed code=preview_prepare_error")
            self._show_generic_error("Could not prepare the preview.")
            return
        self.preview_view.set_settings(state.preview_settings)
        self.preview_view.set_preview_image(state.current_preview_image)
        self._show_stage(AppStage.PREVIEW)
        self._update_controls()

    def _schedule_preview_update(self, settings: PreviewSettings) -> None:
        self._pending_preview_settings = settings
        self.preview_timer.start()

    def _commit_preview_settings(self) -> None:
        try:
            self.session.update_preview_settings(
                mode=self._pending_preview_settings.mode,
                brightness=self._pending_preview_settings.brightness,
                contrast=self._pending_preview_settings.contrast,
                sharpen=self._pending_preview_settings.sharpen,
            )
        except Exception:
            self.privacy_manager.logger.error("event=preview_render status=failed code=preview_render_error")
            self._show_generic_error("Could not update the preview.")
            return
        self.preview_view.set_preview_image(self.session.state.current_preview_image)

    def _back_to_crop(self) -> None:
        self._show_stage(AppStage.CROP)
        self._update_controls()

    def _show_export_dialog(self) -> None:
        request = ExportRequest(
            mode=ExportMode.CUSTOM,
            custom_path=self.session.default_export_path(),
        )

        try:
            exported_path = self.session.export(request)
        except FileExistsError:
            if not self._confirm_overwrite():
                return
            retry_request = replace(request, overwrite=True)
            try:
                exported_path = self.session.export(retry_request)
            except Exception:
                self.privacy_manager.logger.error("event=export status=failed code=export_write_error")
                self._show_generic_error("Export failed.")
                return
        except Exception:
            self.privacy_manager.logger.error("event=export status=failed code=export_write_error")
            self._show_generic_error("Export failed.")
            return

        QMessageBox.information(self, "Export complete", f"Exported BMP to Downloads:\n{exported_path}")

    def _confirm_overwrite(self) -> bool:
        answer = QMessageBox.question(
            self,
            "Overwrite file?",
            "A file already exists at that destination. Replace it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _clear_session(self) -> None:
        self.preview_timer.stop()
        self.session.clear_session()
        self.crop_view.set_display_image(None, None)
        self.preview_view.set_preview_image(None)
        self.preview_view.set_settings(PreviewSettings())
        self._show_stage(AppStage.IMPORT)
        self._update_controls()

    def _show_stage(self, stage: AppStage) -> None:
        index = {
            AppStage.IMPORT: 0,
            AppStage.CROP: 1,
            AppStage.PREVIEW: 2,
        }[stage]
        self.session.state.stage = stage
        self.stack.setCurrentIndex(index)

    def _update_controls(self) -> None:
        active = self.stack.currentIndex() != 0
        self.clear_button.setEnabled(active)

    def _show_generic_error(self, message: str) -> None:
        QMessageBox.warning(self, "X4 Wallpaper Maker", message)

    def perform_shutdown_cleanup(self) -> None:
        if self._shutdown_complete:
            return
        self._shutdown_complete = True
        self.session.shutdown_cleanup()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.perform_shutdown_cleanup()
        super().closeEvent(event)
