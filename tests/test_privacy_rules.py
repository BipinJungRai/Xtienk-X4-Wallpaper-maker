from __future__ import annotations

import io
import logging
import socket
from dataclasses import fields
from pathlib import Path

import pytest
from PIL import Image

from x4_wallpaper_maker.core.privacy_manager import NetworkAccessBlocked, PrivacyManager
from x4_wallpaper_maker.core.session_manager import SessionManager
from x4_wallpaper_maker.models.app_state import AppStage, ExportMode, ExportRequest, SessionState


def _create_source_image(path: Path) -> None:
    Image.new("RGB", (800, 1200), color="navy").save(path, format="PNG")


def test_network_guard_blocks_socket_connections() -> None:
    manager = PrivacyManager()
    manager.configure_logging()
    manager.install_network_guard()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(NetworkAccessBlocked):
        sock.connect(("example.com", 80))


def test_source_path_does_not_end_up_in_session_state(tmp_path: Path) -> None:
    source_path = tmp_path / "private-image.png"
    _create_source_image(source_path)

    session = SessionManager(PrivacyManager())
    session.privacy_manager.configure_logging()
    state = session.import_source(source_path)

    for field in fields(SessionState):
        value = getattr(state, field.name)
        assert str(source_path) not in repr(value)


def test_import_render_export_do_not_create_extra_image_artifacts(tmp_path: Path) -> None:
    source_path = tmp_path / "source.png"
    _create_source_image(source_path)

    session = SessionManager(PrivacyManager())
    session.privacy_manager.configure_logging()
    session.import_source(source_path)
    session.fit_crop((800, 900))
    session.confirm_crop((800, 900))
    export_path = session.export(
        ExportRequest(mode=ExportMode.ROOT_SLEEP, target_directory=tmp_path / "output")
    )

    files = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    assert files == [Path("output/sleep.bmp"), Path("source.png")]
    assert export_path.exists()


def test_logging_omits_source_path(tmp_path: Path) -> None:
    source_path = tmp_path / "secret.png"
    _create_source_image(source_path)

    manager = PrivacyManager()
    manager.configure_logging()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    manager.logger.addHandler(handler)

    session = SessionManager(manager)
    session.import_source(source_path)
    handler.flush()

    assert str(source_path) not in stream.getvalue()


def test_default_export_path_uses_source_name_and_downloads_folder(tmp_path: Path) -> None:
    source_path = tmp_path / "secret family photo.png"
    _create_source_image(source_path)

    session = SessionManager(PrivacyManager())
    session.privacy_manager.configure_logging()
    session.import_source(source_path)

    export_path = session.default_export_path(tmp_path / "Downloads")

    assert export_path == tmp_path / "Downloads" / "secret family photo.bmp"


def test_clear_session_resets_state() -> None:
    stateful_session = SessionManager(PrivacyManager())
    stateful_session.state.stage = AppStage.PREVIEW
    stateful_session.state.current_preview_image = object()

    stateful_session.clear_session()

    assert stateful_session.state.stage == AppStage.IMPORT
    assert stateful_session.state.source_image_rgb is None
    assert stateful_session.state.display_image_rgb is None
    assert stateful_session.state.prepared_base_480x800_rgb is None


def test_rotate_source_turns_images_and_invalidates_prepared_preview(tmp_path: Path) -> None:
    source_path = tmp_path / "rotate-me.png"
    Image.new("RGB", (800, 1200), color="navy").save(source_path, format="PNG")

    session = SessionManager(PrivacyManager())
    session.privacy_manager.configure_logging()
    session.import_source(source_path)
    session.fit_crop((800, 900))
    session.confirm_crop((800, 900))

    state = session.rotate_source(clockwise=True)

    assert state.source_image_rgb.size == (1200, 800)
    assert state.display_image_rgb.size == (1200, 800)
    assert state.stage == AppStage.CROP
    assert state.prepared_base_480x800_rgb is None
    assert state.current_preview_image is None
    assert state.confirmed_crop_box is None
    assert state.crop_draft.scale == 1.0
