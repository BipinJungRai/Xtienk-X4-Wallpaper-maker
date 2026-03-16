"""Central privacy policy controller."""

from __future__ import annotations

import logging
import socket
from typing import Any

from x4_wallpaper_maker.models.app_state import AppStage, CropDraftState, PreviewSettings, SessionState
from x4_wallpaper_maker.utils.secure_cleanup import (
    best_effort_release_pil_image,
    best_effort_release_qt_image,
    force_gc,
    secure_temp_file,
)


class NetworkAccessBlocked(RuntimeError):
    """Raised when code attempts a network call."""


class PrivacyManager:
    """Enforces privacy-sensitive defaults and cleanup behavior."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("x4_wallpaper_maker")
        self._network_guard_installed = False
        self._original_socket_connect = None
        self._original_socket_connect_ex = None
        self._original_create_connection = None

    def configure_startup(self) -> None:
        self.configure_logging()
        self.install_network_guard()
        self.logger.info("event=app_startup status=ok")

    def configure_logging(self) -> None:
        if self.logger.handlers:
            return
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def install_network_guard(self) -> None:
        if self._network_guard_installed:
            return

        def _blocked(*args: Any, **kwargs: Any) -> None:
            raise NetworkAccessBlocked("Network calls are disabled by privacy policy.")

        self._original_socket_connect = socket.socket.connect
        self._original_socket_connect_ex = socket.socket.connect_ex
        self._original_create_connection = socket.create_connection

        socket.socket.connect = _blocked
        socket.socket.connect_ex = _blocked
        socket.create_connection = _blocked
        self._network_guard_installed = True

    def clear_session(self, state: SessionState) -> None:
        for image_attr in ("source_image_rgb", "display_image_rgb", "prepared_base_480x800_rgb"):
            best_effort_release_pil_image(getattr(state, image_attr, None))
            setattr(state, image_attr, None)

        best_effort_release_qt_image(state.current_preview_image)
        state.current_preview_image = None
        state.source_image_stem = None
        state.confirmed_crop_box = None
        state.export_draft = None
        state.import_notice = None
        state.crop_draft = CropDraftState()
        state.preview_settings = PreviewSettings()
        state.stage = AppStage.IMPORT
        state.render_revision += 1

        try:
            from PySide6.QtGui import QPixmapCache

            QPixmapCache.clear()
        except Exception:
            pass

        force_gc()

    def shutdown_cleanup(self, state: SessionState) -> None:
        self.clear_session(state)
        self.logger.info("event=shutdown_cleanup status=ok")

    @property
    def secure_temp_file(self):
        return secure_temp_file
