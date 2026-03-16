"""Pure crop composition helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace

from x4_wallpaper_maker.models.app_state import CropDraftState
from x4_wallpaper_maker.utils.constants import (
    CROP_CANVAS_MARGIN,
    MAX_ZOOM_MULTIPLIER,
    OUTPUT_HEIGHT,
    OUTPUT_WIDTH,
    ZOOM_DEFAULT,
    ZOOM_MAX,
    ZOOM_MIN,
)


@dataclass(frozen=True, slots=True)
class FloatRect:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> tuple[float, float]:
        return self.x + (self.width / 2.0), self.y + (self.height / 2.0)


def compute_crop_rect(canvas_width: int, canvas_height: int, margin: int = CROP_CANVAS_MARGIN) -> FloatRect:
    available_width = max(1.0, float(canvas_width - (margin * 2)))
    available_height = max(1.0, float(canvas_height - (margin * 2)))
    target_ratio = OUTPUT_WIDTH / OUTPUT_HEIGHT

    if available_width / available_height > target_ratio:
        height = available_height
        width = height * target_ratio
    else:
        width = available_width
        height = width / target_ratio

    return FloatRect(
        x=(canvas_width - width) / 2.0,
        y=(canvas_height - height) / 2.0,
        width=width,
        height=height,
    )


def scale_for_zoom(initial_scale: float, zoom_value: int) -> float:
    bounded_zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom_value))
    return initial_scale * (1.0 + ((MAX_ZOOM_MULTIPLIER - 1.0) * (bounded_zoom / float(ZOOM_MAX))))


def zoom_for_scale(initial_scale: float, scale: float) -> int:
    if initial_scale <= 0:
        return ZOOM_DEFAULT
    ratio = max(1.0, scale / initial_scale)
    zoom = int(round(((ratio - 1.0) / (MAX_ZOOM_MULTIPLIER - 1.0)) * ZOOM_MAX))
    return max(ZOOM_MIN, min(ZOOM_MAX, zoom))


def fit_crop_state(image_size: tuple[int, int], canvas_size: tuple[int, int]) -> CropDraftState:
    image_width, image_height = image_size
    crop_rect = compute_crop_rect(*canvas_size)
    fit_scale = max(crop_rect.width / float(image_width), crop_rect.height / float(image_height))
    offset_x = crop_rect.x + ((crop_rect.width - (image_width * fit_scale)) / 2.0)
    offset_y = crop_rect.y + ((crop_rect.height - (image_height * fit_scale)) / 2.0)
    return CropDraftState(
        scale=fit_scale,
        offset_x=offset_x,
        offset_y=offset_y,
        initial_scale=fit_scale,
        initial_offset_x=offset_x,
        initial_offset_y=offset_y,
        zoom_value=ZOOM_DEFAULT,
    )


def clamp_crop_state(image_size: tuple[int, int], canvas_size: tuple[int, int], state: CropDraftState) -> CropDraftState:
    image_width, image_height = image_size
    crop_rect = compute_crop_rect(*canvas_size)
    display_width = image_width * state.scale
    display_height = image_height * state.scale

    if display_width <= crop_rect.width:
        min_x = max_x = crop_rect.x + ((crop_rect.width - display_width) / 2.0)
    else:
        min_x = crop_rect.right - display_width
        max_x = crop_rect.x

    if display_height <= crop_rect.height:
        min_y = max_y = crop_rect.y + ((crop_rect.height - display_height) / 2.0)
    else:
        min_y = crop_rect.bottom - display_height
        max_y = crop_rect.y

    return replace(
        state,
        offset_x=max(min_x, min(max_x, state.offset_x)),
        offset_y=max(min_y, min(max_y, state.offset_y)),
        zoom_value=zoom_for_scale(state.initial_scale, state.scale),
    )


def pan_crop_state(
    image_size: tuple[int, int],
    canvas_size: tuple[int, int],
    state: CropDraftState,
    delta_x: float,
    delta_y: float,
) -> CropDraftState:
    moved = replace(state, offset_x=state.offset_x + delta_x, offset_y=state.offset_y + delta_y)
    return clamp_crop_state(image_size, canvas_size, moved)


def zoom_crop_state(
    image_size: tuple[int, int],
    canvas_size: tuple[int, int],
    state: CropDraftState,
    zoom_value: int,
    anchor: tuple[float, float] | None = None,
) -> CropDraftState:
    crop_rect = compute_crop_rect(*canvas_size)
    anchor_x, anchor_y = anchor or crop_rect.center
    new_scale = scale_for_zoom(state.initial_scale, zoom_value)

    if state.scale <= 0:
        local_x = 0.0
        local_y = 0.0
    else:
        local_x = (anchor_x - state.offset_x) / state.scale
        local_y = (anchor_y - state.offset_y) / state.scale

    updated = replace(
        state,
        scale=new_scale,
        offset_x=anchor_x - (local_x * new_scale),
        offset_y=anchor_y - (local_y * new_scale),
        zoom_value=max(ZOOM_MIN, min(ZOOM_MAX, zoom_value)),
    )
    return clamp_crop_state(image_size, canvas_size, updated)


def resolve_crop_box(image_size: tuple[int, int], canvas_size: tuple[int, int], state: CropDraftState) -> tuple[float, float, float, float]:
    crop_rect = compute_crop_rect(*canvas_size)
    left = max(0.0, min(float(image_size[0]), (crop_rect.x - state.offset_x) / state.scale))
    top = max(0.0, min(float(image_size[1]), (crop_rect.y - state.offset_y) / state.scale))
    right = max(left + 1.0, min(float(image_size[0]), (crop_rect.right - state.offset_x) / state.scale))
    bottom = max(top + 1.0, min(float(image_size[1]), (crop_rect.bottom - state.offset_y) / state.scale))

    width, height = image_size
    return (
        left / float(width),
        top / float(height),
        right / float(width),
        bottom / float(height),
    )

