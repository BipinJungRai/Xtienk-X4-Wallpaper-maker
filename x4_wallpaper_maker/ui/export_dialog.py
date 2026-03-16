"""Export dialog UI."""

from __future__ import annotations

from pathlib import Path

from x4_wallpaper_maker.models.app_state import ExportMode, ExportRequest, SleepFolderVariant
from x4_wallpaper_maker.utils.constants import DEFAULT_EXPORT_FILENAME
from x4_wallpaper_maker.utils.drive_detection import DriveInfo, list_mounted_volumes
from x4_wallpaper_maker.utils.file_dialogs import select_directory, select_save_file

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ExportDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export wallpaper")
        self.setModal(True)
        self.resize(560, 360)

        self._drives: list[DriveInfo] = list_mounted_volumes()
        self._selected_path: Path | None = None
        self._request: ExportRequest | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.form = QFormLayout()
        self.form.setHorizontalSpacing(16)
        self.form.setVerticalSpacing(14)

        self.mode_combo = QComboBox(self)
        self.mode_combo.addItem("sleep.bmp", ExportMode.ROOT_SLEEP)
        self.mode_combo.addItem(".sleep folder", ExportMode.DOT_SLEEP_FOLDER)
        self.mode_combo.addItem("sleep folder", ExportMode.SLEEP_FOLDER)
        self.mode_combo.addItem("Custom BMP", ExportMode.CUSTOM)
        self.mode_combo.currentIndexChanged.connect(self._refresh_mode_ui)
        self.form.addRow("Export mode", self.mode_combo)

        volume_row = QWidget(self)
        volume_layout = QHBoxLayout(volume_row)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(8)
        self.volume_combo = QComboBox(volume_row)
        self.volume_combo.addItem("No detected volume", None)
        for drive in self._drives:
            self.volume_combo.addItem(drive.label, drive.path)
        self.use_volume_button = QPushButton("Use selected", volume_row)
        self.use_volume_button.clicked.connect(self._use_selected_volume)
        volume_layout.addWidget(self.volume_combo, stretch=1)
        volume_layout.addWidget(self.use_volume_button)
        self.form.addRow("Detected SD card", volume_row)

        destination_row = QWidget(self)
        destination_layout = QHBoxLayout(destination_row)
        destination_layout.setContentsMargins(0, 0, 0, 0)
        destination_layout.setSpacing(8)
        self.destination_edit = QLineEdit(destination_row)
        self.destination_edit.setReadOnly(True)
        self.browse_button = QPushButton("Browse", destination_row)
        self.browse_button.clicked.connect(self._browse)
        destination_layout.addWidget(self.destination_edit, stretch=1)
        destination_layout.addWidget(self.browse_button)
        self.form.addRow("Destination", destination_row)

        self.filename_edit = QLineEdit(DEFAULT_EXPORT_FILENAME, self)
        self.form.addRow("File name", self.filename_edit)

        layout.addLayout(self.form)

        note = QLabel("Metadata stripped. No image history saved.")
        note.setWordWrap(True)
        note.setObjectName("helperLabel")
        layout.addWidget(note)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok, parent=self)
        self.buttons.accepted.connect(self._accept)
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Export now")
        layout.addWidget(self.buttons)

        self._refresh_mode_ui()

    def export_request(self) -> ExportRequest | None:
        return self._request

    def _use_selected_volume(self) -> None:
        path = self.volume_combo.currentData()
        if path is not None:
            self._selected_path = Path(path)
            self.destination_edit.setText(str(self._selected_path))

    def _browse(self) -> None:
        mode = self.mode_combo.currentData()
        if mode == ExportMode.CUSTOM:
            default_dir = self._selected_path if self._selected_path is not None else Path.home() / DEFAULT_EXPORT_FILENAME
            selected = select_save_file(self, "Choose export destination", default_dir, "Bitmap images (*.bmp)")
            if selected is not None:
                self._selected_path = selected
                self.destination_edit.setText(str(selected))
            return

        selected = select_directory(self, "Choose export destination")
        if selected is not None:
            self._selected_path = selected
            self.destination_edit.setText(str(selected))

    def _refresh_mode_ui(self) -> None:
        mode = self.mode_combo.currentData()
        uses_file_name = mode in {ExportMode.DOT_SLEEP_FOLDER, ExportMode.SLEEP_FOLDER}
        self.filename_edit.setVisible(uses_file_name)
        label = self.form.labelForField(self.filename_edit)
        if label is not None:
            label.setVisible(uses_file_name)

    def _accept(self) -> None:
        mode = self.mode_combo.currentData()
        if self._selected_path is None:
            self.buttons.button(QDialogButtonBox.StandardButton.Ok).setFocus()
            return

        if mode == ExportMode.CUSTOM:
            self._request = ExportRequest(mode=ExportMode.CUSTOM, custom_path=self._selected_path)
            self.accept()
            return

        if mode == ExportMode.ROOT_SLEEP:
            self._request = ExportRequest(mode=ExportMode.ROOT_SLEEP, target_directory=self._selected_path)
            self.accept()
            return

        variant = SleepFolderVariant.DOT_SLEEP if mode == ExportMode.DOT_SLEEP_FOLDER else SleepFolderVariant.SLEEP
        export_mode = ExportMode.DOT_SLEEP_FOLDER if variant == SleepFolderVariant.DOT_SLEEP else ExportMode.SLEEP_FOLDER
        self._request = ExportRequest(
            mode=export_mode,
            target_directory=self._selected_path,
            file_name=self.filename_edit.text().strip() or DEFAULT_EXPORT_FILENAME,
            folder_variant=variant,
        )
        self.accept()
