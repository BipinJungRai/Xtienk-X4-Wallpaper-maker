"""Privacy-safe Qt file dialog helpers."""

from __future__ import annotations

from pathlib import Path


def _dialog_base(parent):
    from PySide6.QtWidgets import QFileDialog

    dialog = QFileDialog(parent)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setHistory([])
    return dialog


def select_import_file(parent, title: str, name_filter: str) -> Path | None:
    from PySide6.QtWidgets import QFileDialog

    dialog = _dialog_base(parent)
    dialog.setWindowTitle(title)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setNameFilter(name_filter)
    if dialog.exec() != QFileDialog.DialogCode.Accepted:
        return None
    files = dialog.selectedFiles()
    return Path(files[0]) if files else None


def select_directory(parent, title: str) -> Path | None:
    from PySide6.QtWidgets import QFileDialog

    dialog = _dialog_base(parent)
    dialog.setWindowTitle(title)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
    if dialog.exec() != QFileDialog.DialogCode.Accepted:
        return None
    files = dialog.selectedFiles()
    return Path(files[0]) if files else None


def select_save_file(parent, title: str, default_path: Path, name_filter: str) -> Path | None:
    from PySide6.QtWidgets import QFileDialog

    dialog = _dialog_base(parent)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setWindowTitle(title)
    dialog.setDirectory(str(default_path.parent))
    dialog.selectFile(default_path.name)
    dialog.setNameFilter(name_filter)
    if dialog.exec() != QFileDialog.DialogCode.Accepted:
        return None
    files = dialog.selectedFiles()
    return Path(files[0]) if files else None
