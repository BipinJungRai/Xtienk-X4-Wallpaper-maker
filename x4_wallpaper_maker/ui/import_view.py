"""Import stage UI."""

from __future__ import annotations

from pathlib import Path

from x4_wallpaper_maker.utils.constants import SUPPORTED_INPUT_EXTENSIONS


def _first_supported_path(mime_data) -> str | None:
    if not mime_data.hasUrls():
        return None
    for url in mime_data.urls():
        if not url.isLocalFile():
            continue
        path = Path(url.toLocalFile())
        if path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS:
            return str(path)
    return None


from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class DropZoneFrame(QFrame):
    fileDropped = Signal(str)
    selectRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(56, 56, 56, 56)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("Drop an image here")
        self.title_label.setObjectName("heroTitle")
        self.subtitle_label = QLabel("or choose a file")
        self.subtitle_label.setObjectName("heroSubtitle")
        self.select_button = QPushButton("Select Image")
        self.select_button.setObjectName("primaryButton")
        self.helper_label = QLabel("Processed locally. Nothing uploaded.")
        self.helper_label.setObjectName("helperLabel")

        self.select_button.clicked.connect(self.selectRequested.emit)

        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.select_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.helper_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if _first_supported_path(event.mimeData()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        path = _first_supported_path(event.mimeData())
        if path is None:
            event.ignore()
            return
        self.fileDropped.emit(path)
        event.acceptProposedAction()


class ImportView(QWidget):
    fileDropped = Signal(str)
    selectRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 48, 80, 48)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drop_zone = DropZoneFrame(self)
        self.drop_zone.setMinimumSize(600, 420)
        self.drop_zone.fileDropped.connect(self.fileDropped.emit)
        self.drop_zone.selectRequested.connect(self.selectRequested.emit)
        layout.addWidget(self.drop_zone, alignment=Qt.AlignmentFlag.AlignCenter)
