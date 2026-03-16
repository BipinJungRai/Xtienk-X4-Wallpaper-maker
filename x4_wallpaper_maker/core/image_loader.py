"""Image loading routines with privacy-oriented defaults."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from x4_wallpaper_maker.utils.constants import DISPLAY_IMAGE_MAX_DIMENSION


def load_source_image(path: str | Path) -> tuple[Image.Image, Image.Image, str | None]:
    """Load an image into fresh RGB buffers and drop metadata."""
    image_path = Path(path)
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

