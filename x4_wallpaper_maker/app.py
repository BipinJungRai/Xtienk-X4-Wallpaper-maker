"""Application entrypoint."""

from __future__ import annotations

import sys

from x4_wallpaper_maker.core.privacy_manager import PrivacyManager
from x4_wallpaper_maker.utils.constants import APP_TITLE


def _install_exception_hook(privacy_manager: PrivacyManager) -> None:
    def _handle_exception(_exc_type, _exc_value, _exc_traceback) -> None:
        privacy_manager.logger.error("event=fatal_ui_exception status=failed code=unhandled_exception")
        try:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(None, APP_TITLE, "The app hit an unexpected error and has reset the session.")
        except Exception:
            pass

    sys.excepthook = _handle_exception


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError("PySide6 is required to run X4 Wallpaper Maker.") from exc
    from x4_wallpaper_maker.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)

    privacy_manager = PrivacyManager()
    privacy_manager.configure_startup()
    _install_exception_hook(privacy_manager)

    window = MainWindow(privacy_manager=privacy_manager)
    app.aboutToQuit.connect(window.perform_shutdown_cleanup)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
