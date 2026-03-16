"""Best-effort cleanup helpers.

These routines are intentionally conservative. Python and Qt do not allow a
general guarantee that all image bytes are zeroized, so the app treats cleanup
as a best-effort privacy measure rather than a perfect claim.
"""

from __future__ import annotations

import gc
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def best_effort_clear_bytearray(buffer: bytearray | None) -> None:
    """Overwrite a mutable buffer if one exists."""
    if buffer is None:
        return
    for index in range(len(buffer)):
        buffer[index] = 0


def best_effort_release_pil_image(image: object | None) -> None:
    """Close Pillow images if they expose a close method."""
    if image is None:
        return
    close = getattr(image, "close", None)
    if callable(close):
        close()


def best_effort_release_qt_image(image: object | None) -> None:
    """Detach Qt image references without assuming a specific Qt type."""
    if image is None:
        return
    detach = getattr(image, "detach", None)
    if callable(detach):
        detach()


def force_gc() -> None:
    """Run Python garbage collection for a small privacy benefit."""
    gc.collect()


@contextmanager
def secure_temp_file(suffix: str = "", prefix: str = "x4wm-") -> Iterator[Path]:
    """Create a secure temporary file path for future unavoidable platform paths.

    v1 does not use temporary image files during normal operation. This helper
    exists to centralize restrictive temp-file behavior if a future platform
    integration requires one.
    """

    fd, raw_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    try:
        os.fchmod(fd, 0o600)
        yield Path(raw_path)
    finally:
        os.close(fd)
        try:
            Path(raw_path).unlink(missing_ok=True)
        except OSError:
            pass

