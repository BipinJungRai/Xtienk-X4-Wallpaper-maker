from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw

from x4_wallpaper_maker.core import render_engine
from x4_wallpaper_maker.models.app_state import PreviewSettings, RenderMode


def _gradient_image(width: int = 480, height: int = 800) -> Image.Image:
    image = Image.new("RGB", (width, height))
    for x in range(width):
        shade = int((x / max(1, width - 1)) * 255)
        for y in range(height):
            image.putpixel((x, y), (shade, shade, shade))
    return image


def test_prepare_base_image_resizes_to_x4_output() -> None:
    source = Image.new("RGB", (1000, 1000), "white")
    prepared = render_engine.prepare_base_image(source, (0.1, 0.2, 0.9, 0.95))
    assert prepared.size == (480, 800)


def test_standard_grayscale_render_is_deterministic() -> None:
    base = _gradient_image()
    settings = PreviewSettings(mode=RenderMode.STANDARD)
    first = render_engine.render_preview(base, settings)
    second = render_engine.render_preview(base, settings)

    assert first.mode == "L"
    assert list(first.getdata()) == list(second.getdata())


def test_dithered_render_differs_from_standard() -> None:
    base = _gradient_image()
    standard = render_engine.render_preview(base, PreviewSettings(mode=RenderMode.STANDARD))
    dithered = render_engine.render_preview(base, PreviewSettings(mode=RenderMode.DITHERED))

    assert set(dithered.getdata()).issubset({0, 255})
    assert ImageChops.difference(standard, dithered).getbbox() is not None


def test_mono_threshold_then_brightness_keeps_strict_pipeline_order() -> None:
    base = Image.new("RGB", (480, 800), (128, 128, 128))
    rendered = render_engine.render_export_bitmap(
        base,
        PreviewSettings(mode=RenderMode.MONO, brightness=-50, contrast=0, sharpen=False),
    )

    pixel = rendered.getpixel((100, 100))
    assert 0 < pixel < 255


def test_sharpen_toggle_changes_output() -> None:
    base = Image.new("RGB", (480, 800), "gray")
    drawer = ImageDraw.Draw(base)
    drawer.rectangle((150, 200, 330, 600), fill="white")

    plain = render_engine.render_preview(base, PreviewSettings(mode=RenderMode.STANDARD, sharpen=False))
    sharpened = render_engine.render_preview(base, PreviewSettings(mode=RenderMode.STANDARD, sharpen=True))

    assert ImageChops.difference(plain, sharpened).getbbox() is not None

