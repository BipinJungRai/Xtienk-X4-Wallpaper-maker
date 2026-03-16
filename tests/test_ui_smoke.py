from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

PySide6 = pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from x4_wallpaper_maker.core.privacy_manager import PrivacyManager
from x4_wallpaper_maker.ui.main_window import MainWindow


def _create_source_image(path: Path) -> None:
    Image.new("RGB", (900, 1400), color="teal").save(path, format="PNG")


def test_stage_flow_and_clear_session(qtbot, tmp_path: Path) -> None:
    source_path = tmp_path / "ui-source.png"
    _create_source_image(source_path)

    manager = PrivacyManager()
    manager.configure_logging()
    window = MainWindow(privacy_manager=manager)
    qtbot.addWidget(window)
    window.show()

    window._import_image(str(source_path))
    qtbot.waitUntil(lambda: window.stack.currentIndex() == 1)

    window._fit_crop()
    qtbot.mouseClick(window.crop_view.continue_button, PySide6.QtCore.Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.stack.currentIndex() == 2)

    qtbot.mouseClick(window.clear_button, PySide6.QtCore.Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.stack.currentIndex() == 0)
