"""Preview stage UI."""

from __future__ import annotations

from x4_wallpaper_maker.models.app_state import PreviewSettings, RenderMode

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class DevicePreviewWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(420, 520)
        self._pixmap: QPixmap | None = None

    def set_preview_image(self, image: QImage | None) -> None:
        self._pixmap = QPixmap.fromImage(image) if image is not None else None
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), QColor("#efe6d6"))

            outer_margin = 36
            outer_rect = self.rect().adjusted(outer_margin, outer_margin, -outer_margin, -outer_margin)
            painter.setBrush(QColor("#d7d0c5"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(outer_rect, 34, 34)

            inner_margin_x = 48
            inner_margin_y = 58
            screen_rect = outer_rect.adjusted(inner_margin_x, inner_margin_y, -inner_margin_x, -inner_margin_y)
            painter.setBrush(QColor("#f2eee8"))
            painter.drawRoundedRect(screen_rect, 18, 18)

            if self._pixmap is not None:
                scaled = self._pixmap.scaled(
                    screen_rect.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                x = screen_rect.x() + ((screen_rect.width() - scaled.width()) / 2)
                y = screen_rect.y() + ((screen_rect.height() - scaled.height()) / 2)
                clip_path = QPainterPath()
                clip_path.addRoundedRect(screen_rect, 18, 18)
                painter.setClipPath(clip_path)
                painter.drawPixmap(int(round(x)), int(round(y)), scaled)
                painter.setClipping(False)
        finally:
            painter.end()


class PreviewView(QWidget):
    settingsEdited = Signal(object)
    backRequested = Signal()
    exportRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._syncing = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        self.preview_widget = DevicePreviewWidget(self)
        layout.addWidget(self.preview_widget, stretch=1)

        panel = QFrame(self)
        panel.setObjectName("sidePanel")
        panel.setFixedWidth(300)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(16)

        title = QLabel("Preview")
        title.setObjectName("sectionTitle")
        panel_layout.addWidget(title)

        self.brightness_slider = self._build_slider(panel_layout, "Brightness")
        self.contrast_slider = self._build_slider(panel_layout, "Contrast")

        mode_label = QLabel("Mode")
        mode_label.setObjectName("fieldLabel")
        panel_layout.addWidget(mode_label)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        self.mode_group = QButtonGroup(self)
        self.mode_buttons: dict[RenderMode, QPushButton] = {}
        for label, mode in (("Standard", RenderMode.STANDARD), ("Dithered", RenderMode.DITHERED), ("Mono", RenderMode.MONO)):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setObjectName("modeButton")
            self.mode_group.addButton(button)
            self.mode_buttons[mode] = button
            mode_row.addWidget(button)
        self.mode_group.buttonClicked.connect(self._emit_settings)
        panel_layout.addLayout(mode_row)

        self.advanced_toggle = QToolButton(panel)
        self.advanced_toggle.setText("Advanced")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        self.advanced_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.advanced_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        panel_layout.addWidget(self.advanced_toggle)

        self.advanced_panel = QWidget(panel)
        advanced_layout = QVBoxLayout(self.advanced_panel)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        self.sharpen_checkbox = QCheckBox("Sharpen edges", self.advanced_panel)
        self.sharpen_checkbox.toggled.connect(self._emit_settings)
        advanced_layout.addWidget(self.sharpen_checkbox)
        self.advanced_panel.hide()
        panel_layout.addWidget(self.advanced_panel)

        panel_layout.addStretch(1)

        self.export_button = QPushButton("Export to Downloads")
        self.export_button.setObjectName("primaryButton")
        self.back_button = QPushButton("Back to crop")
        self.export_button.clicked.connect(self.exportRequested.emit)
        self.back_button.clicked.connect(self.backRequested.emit)
        panel_layout.addWidget(self.export_button)
        panel_layout.addWidget(self.back_button)

        layout.addWidget(panel)

        self.brightness_slider.valueChanged.connect(self._emit_settings)
        self.contrast_slider.valueChanged.connect(self._emit_settings)
        self.mode_buttons[RenderMode.STANDARD].setChecked(True)

    def _build_slider(self, parent_layout: QVBoxLayout, title: str) -> QSlider:
        label = QLabel(title)
        label.setObjectName("fieldLabel")
        parent_layout.addWidget(label)
        slider = QSlider(Qt.Orientation.Horizontal, self)
        slider.setRange(-50, 50)
        slider.setValue(0)
        parent_layout.addWidget(slider)
        return slider

    def _toggle_advanced(self, checked: bool) -> None:
        self.advanced_toggle.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        self.advanced_panel.setVisible(checked)

    def _emit_settings(self, *_args) -> None:
        if self._syncing:
            return
        self.settingsEdited.emit(self.current_settings())

    def current_settings(self) -> PreviewSettings:
        selected_mode = RenderMode.STANDARD
        for mode, button in self.mode_buttons.items():
            if button.isChecked():
                selected_mode = mode
                break
        return PreviewSettings(
            mode=selected_mode,
            brightness=self.brightness_slider.value(),
            contrast=self.contrast_slider.value(),
            sharpen=self.sharpen_checkbox.isChecked(),
        )

    def set_settings(self, settings: PreviewSettings) -> None:
        self._syncing = True
        try:
            self.brightness_slider.setValue(settings.brightness)
            self.contrast_slider.setValue(settings.contrast)
            for mode, button in self.mode_buttons.items():
                button.setChecked(mode == settings.mode)
            self.sharpen_checkbox.setChecked(settings.sharpen)
        finally:
            self._syncing = False

    def set_preview_image(self, image: QImage | None) -> None:
        self.preview_widget.set_preview_image(image)
