from __future__ import annotations

import math

from x4_wallpaper_maker.core import crop_engine


def test_compute_crop_rect_keeps_x4_ratio() -> None:
    rect = crop_engine.compute_crop_rect(900, 700)
    assert math.isclose(rect.width / rect.height, 480 / 800, rel_tol=1e-4)


def test_fit_crop_state_covers_crop_rect_for_landscape_source() -> None:
    state = crop_engine.fit_crop_state((1600, 900), (900, 700))
    crop_rect = crop_engine.compute_crop_rect(900, 700)

    assert (1600 * state.scale) >= crop_rect.width
    assert (900 * state.scale) >= crop_rect.height
    assert state.zoom_value == 0


def test_pan_crop_state_is_clamped_to_cover_crop_area() -> None:
    initial = crop_engine.fit_crop_state((1200, 1200), (800, 900))
    moved = crop_engine.pan_crop_state((1200, 1200), (800, 900), initial, delta_x=1000, delta_y=-1000)
    crop_rect = crop_engine.compute_crop_rect(800, 900)

    assert moved.offset_x <= crop_rect.x
    assert moved.offset_y <= crop_rect.y
    assert moved.offset_x + (1200 * moved.scale) >= crop_rect.right
    assert moved.offset_y + (1200 * moved.scale) >= crop_rect.bottom


def test_resolve_crop_box_returns_normalized_box() -> None:
    state = crop_engine.fit_crop_state((600, 1000), (800, 900))
    box = crop_engine.resolve_crop_box((600, 1000), (800, 900), state)

    assert box[0] >= 0.0
    assert box[1] >= 0.0
    assert box[2] <= 1.0
    assert box[3] <= 1.0
    assert box[2] > box[0]
    assert box[3] > box[1]

