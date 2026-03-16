"""Image loading routines with privacy-oriented defaults."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from x4_wallpaper_maker.utils.constants import DISPLAY_IMAGE_MAX_DIMENSION

_HEIF_EXTENSIONS = {".heic", ".heif"}
_HEIF_OPENER_REGISTERED = False


class SourceImageLoadError(RuntimeError):
    """Raised when the source image cannot be loaded with the available decoders."""


def _register_heif_opener() -> None:
    from pillow_heif import register_heif_opener

    register_heif_opener()


def _ensure_heif_support(image_path: Path) -> None:
    if image_path.suffix.lower() not in _HEIF_EXTENSIONS:
        return

    global _HEIF_OPENER_REGISTERED
    if _HEIF_OPENER_REGISTERED:
        return

    try:
        _register_heif_opener()
    except ImportError as exc:
        raise SourceImageLoadError(
            "HEIC support is not available yet. Reinstall the app dependencies to enable HEIC/HEIF import."
        ) from exc

    _HEIF_OPENER_REGISTERED = True


def load_source_image(path: str | Path) -> tuple[Image.Image, Image.Image, str | None]:
    """Load an image into fresh RGB buffers and drop metadata."""
    image_path = Path(path)
    _ensure_heif_support(image_path)
    with Image.open(image_path) as opened:
        animated = bool(getattr(opened, "is_animated", False)) and int(getattr(opened, "n_frames", 1)) > 1
        try:
            opened.seek(0)
        except EOFError:
            pass
        normalized = ImageOps.exif_transpose(opened)
        source_image = normalized.convert("RGB").copy()

    display_image = source_image.copy()
    display_image.thumbnail((DISPLAY_IMAGE_MAX_DIMENSION, DISPLAY_IMAGE_MAX_DIMENSION), Image.Resampling.LANCZOS)

    notice = None
    if animated and image_path.suffix.lower() == ".webp":
        notice = "Animated WEBP imported using the first frame only."

    return source_image, display_image, notice
