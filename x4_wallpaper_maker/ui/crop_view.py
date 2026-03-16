"""Crop stage UI."""

from __future__ import annotations

from PIL import Image

from x4_wallpaper_maker.core import crop_engine
from x4_wallpaper_maker.models.app_state import CropDraftState

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


def _pil_to_qpixmap(image: Image.Image) -> QPixmap:
    rgb = image.convert("RGB")
    payload = rgb.tobytes("raw", "RGB")
    qimage = QImage(payload, rgb.width, rgb.height, rgb.width * 3, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimage.copy())


class CropCanvas(QWidget):
    draftEdited = Signal(object)
    fitRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(520, 520)
        self.setMouseTracking(True)
        self._pixmap: QPixmap | None = None
        self._image_size: tuple[int, int] | None = None
        self._draft = CropDraftState()
        self._dragging = False
        self._last_mouse_pos = QPointF()
        self._needs_fit = False

    def set_display_image(self, image: Image.Image | None) -> None:
        self._pixmap = _pil_to_qpixmap(image) if image is not None else None
        self._image_size = image.size if image is not None else None
        self._needs_fit = image is not None
        self.update()
        if self._needs_fit and self.width() > 0 and self.height() > 0:
            self.fitRequested.emit()

    def set_draft_state(self, draft: CropDraftState) -> None:
        self._draft = draft
        self._needs_fit = False
        self.update()

    def canvas_size(self) -> tuple[int, int]:
        return self.width(), self.height()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._pixmap is not None and self._needs_fit:
            self.fitRequested.emit()
            return
        if self._pixmap is not None and self._image_size is not None:
            self._draft = crop_engine.clamp_crop_state(self._image_size, self.canvas_size(), self._draft)
            self.draftEdited.emit(self._draft)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._pixmap is not None:
            self._dragging = True
            self._last_mouse_pos = event.position()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not self._dragging or self._image_size is None:
            super().mouseMoveEvent(event)
            return
        current_pos = event.position()
        delta = current_pos - self._last_mouse_pos
        self._last_mouse_pos = current_pos
        self._draft = crop_engine.pan_crop_state(self._image_size, self.canvas_size(), self._draft, delta.x(), delta.y())
        self.draftEdited.emit(self._draft)
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._image_size is None:
            return
        step = 5 if event.angleDelta().y() > 0 else -5
        zoom_value = max(0, min(100, self._draft.zoom_value + step))
        anchor = (event.position().x(), event.position().y())
        self._draft = crop_engine.zoom_crop_state(self._image_size, self.canvas_size(), self._draft, zoom_value, anchor=anchor)
        self.draftEdited.emit(self._draft)
        self.update()
        event.accept()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#efe6d6"))

        crop_rect = crop_engine.compute_crop_rect(self.width(), self.height())
        if self._pixmap is not None and self._image_size is not None:
            target_x = self._draft.offset_x
            target_y = self._draft.offset_y
            target_w = self._image_size[0] * self._draft.scale
            target_h = self._image_size[1] * self._draft.scale
            painter.drawPixmap(int(round(target_x)), int(round(target_y)), int(round(target_w)), int(round(target_h)), self._pixmap)

        overlay_path = QPainterPath()
        overlay_path.addRect(float(self.rect().x()), float(self.rect().y()), float(self.rect().width()), float(self.rect().height()))
        hole_path = QPainterPath()
        hole_path.addRoundedRect(crop_rect.x, crop_rect.y, crop_rect.width, crop_rect.height, 18, 18)
        painter.fillPath(overlay_path.subtracted(hole_path), QColor(0, 0, 0, 110))

        border_pen = QPen(QColor("#fff8ef"))
        border_pen.setWidth(3)
        painter.setPen(border_pen)
        painter.drawRoundedRect(crop_rect.x, crop_rect.y, crop_rect.width, crop_rect.height, 18, 18)

        guide_pen = QPen(QColor(255, 255, 255, 90))
        guide_pen.setWidth(1)
        painter.setPen(guide_pen)
        painter.drawLine(crop_rect.x, crop_rect.y + (crop_rect.height / 2.0), crop_rect.right, crop_rect.y + (crop_rect.height / 2.0))
        painter.drawLine(crop_rect.x + (crop_rect.width / 2.0), crop_rect.y, crop_rect.x + (crop_rect.width / 2.0), crop_rect.bottom)


class CropView(QWidget):
    fitRequested = Signal()
    resetRequested = Signal()
    continueRequested = Signal()
    backRequested = Signal()
    zoomChanged = Signal(int)
    draftEdited = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        self.canvas = CropCanvas(self)
        self.canvas.fitRequested.connect(self.fitRequested.emit)
        self.canvas.draftEdited.connect(self.draftEdited.emit)
        layout.addWidget(self.canvas, stretch=1)

        panel = QFrame(self)
        panel.setObjectName("sidePanel")
        panel.setFixedWidth(280)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(16)

        title = QLabel("Crop")
        title.setObjectName("sectionTitle")
        panel_layout.addWidget(title)

        self.notice_label = QLabel("")
        self.notice_label.setWordWrap(True)
        self.notice_label.setObjectName("helperLabel")
        self.notice_label.hide()
        panel_layout.addWidget(self.notice_label)

        zoom_label = QLabel("Zoom")
        zoom_label.setObjectName("fieldLabel")
        panel_layout.addWidget(zoom_label)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal, panel)
        self.zoom_slider.setRange(0, 100)
        self.zoom_slider.valueChanged.connect(self.zoomChanged.emit)
        panel_layout.addWidget(self.zoom_slider)

        self.reset_button = QPushButton("Reset")
        self.fit_button = QPushButton("Fit")
        self.continue_button = QPushButton("Continue")
        self.continue_button.setObjectName("primaryButton")
        self.back_button = QPushButton("Back")

        self.reset_button.clicked.connect(self.resetRequested.emit)
        self.fit_button.clicked.connect(self.fitRequested.emit)
        self.continue_button.clicked.connect(self.continueRequested.emit)
        self.back_button.clicked.connect(self.backRequested.emit)

        panel_layout.addWidget(self.reset_button)
        panel_layout.addWidget(self.fit_button)
        panel_layout.addWidget(QLabel("Output: 480 × 800"))
        panel_layout.addStretch(1)
        panel_layout.addWidget(self.continue_button)
        panel_layout.addWidget(self.back_button)

        layout.addWidget(panel)

    def set_display_image(self, image: Image.Image | None, notice: str | None = None) -> None:
        self.canvas.set_display_image(image)
        if notice:
            self.notice_label.setText(notice)
            self.notice_label.show()
        else:
            self.notice_label.hide()

    def set_draft_state(self, draft: CropDraftState) -> None:
        self.canvas.set_draft_state(draft)
        blocked = self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(draft.zoom_value)
        self.zoom_slider.blockSignals(blocked)

    def canvas_size(self) -> tuple[int, int]:
        return self.canvas.canvas_size()
