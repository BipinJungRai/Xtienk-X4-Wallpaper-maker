"""Image rendering pipeline."""

from __future__ import annotations

from PIL import Image, ImageEnhance, ImageFilter

from x4_wallpaper_maker.models.app_state import PreviewSettings, RenderMode
from x4_wallpaper_maker.utils.constants import MONO_THRESHOLD, OUTPUT_SIZE


def _slider_to_factor(value: int) -> float:
    bounded = max(-50, min(50, value))
    return 1.0 + (bounded / 100.0)


def prepare_base_image(source_image_rgb: Image.Image, normalized_crop_box: tuple[float, float, float, float]) -> Image.Image:
    width, height = source_image_rgb.size
    left = int(round(normalized_crop_box[0] * width))
    top = int(round(normalized_crop_box[1] * height))
    right = int(round(normalized_crop_box[2] * width))
    bottom = int(round(normalized_crop_box[3] * height))

    left = max(0, min(width - 1, left))
    top = max(0, min(height - 1, top))
    right = max(left + 1, min(width, right))
    bottom = max(top + 1, min(height, bottom))

    cropped = source_image_rgb.crop((left, top, right, bottom))
    return cropped.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)


def _apply_mode(grayscale_image: Image.Image, mode: RenderMode) -> Image.Image:
    if mode == RenderMode.DITHERED:
        return grayscale_image.convert("1", dither=Image.Dither.FLOYDSTEINBERG).convert("L")
    if mode == RenderMode.MONO:
        return grayscale_image.point(lambda value: 255 if value >= MONO_THRESHOLD else 0, mode="L")
    return grayscale_image


def _apply_adjustments(image: Image.Image, settings: PreviewSettings) -> Image.Image:
    adjusted = image
    if settings.brightness:
        adjusted = ImageEnhance.Brightness(adjusted).enhance(_slider_to_factor(settings.brightness))
    if settings.contrast:
        adjusted = ImageEnhance.Contrast(adjusted).enhance(_slider_to_factor(settings.contrast))
    if settings.sharpen:
        adjusted = adjusted.filter(ImageFilter.UnsharpMask(radius=1, percent=130, threshold=2))
    return adjusted


def _render(base_image_rgb: Image.Image, settings: PreviewSettings) -> Image.Image:
    grayscale = base_image_rgb.convert("L")
    mode_applied = _apply_mode(grayscale, settings.mode)
    return _apply_adjustments(mode_applied, settings)


def render_preview(base_image_rgb: Image.Image, settings: PreviewSettings) -> Image.Image:
    return _render(base_image_rgb, settings)


def render_export_bitmap(base_image_rgb: Image.Image, settings: PreviewSettings) -> Image.Image:
    return _render(base_image_rgb, settings)

