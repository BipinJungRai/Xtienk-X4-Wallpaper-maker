"""Shared constants for the application."""

from __future__ import annotations

from pathlib import Path

APP_TITLE = "X4 Wallpaper Maker"
OUTPUT_WIDTH = 480
OUTPUT_HEIGHT = 800
OUTPUT_SIZE = (OUTPUT_WIDTH, OUTPUT_HEIGHT)
OUTPUT_ASPECT_WIDTH = 3
OUTPUT_ASPECT_HEIGHT = 5

SUPPORTED_INPUT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".heif"}
SUPPORTED_INPUT_NAME_FILTER = "Images (*.jpg *.jpeg *.png *.webp *.bmp *.heic *.heif)"
DEFAULT_EXPORT_FILENAME = "x4-wallpaper.bmp"
ROOT_SLEEP_FILENAME = "sleep.bmp"
DOT_SLEEP_DIRECTORY = ".sleep"
SLEEP_DIRECTORY = "sleep"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 820
MIN_WINDOW_WIDTH = 1120
MIN_WINDOW_HEIGHT = 760

CROP_CANVAS_MARGIN = 32
CROP_PANEL_WIDTH = 280
PREVIEW_PANEL_WIDTH = 300
PREVIEW_DEBOUNCE_MS = 120
DISPLAY_IMAGE_MAX_DIMENSION = 1600
MAX_ZOOM_MULTIPLIER = 4.0

BRIGHTNESS_MIN = -50
BRIGHTNESS_MAX = 50
CONTRAST_MIN = -50
CONTRAST_MAX = 50
SLIDER_DEFAULT = 0
ZOOM_MIN = 0
ZOOM_MAX = 100
ZOOM_DEFAULT = 0
MONO_THRESHOLD = 128

PALETTE = {
    "window": "#f5efe3",
    "panel": "#fffaf0",
    "panel_alt": "#f0e7d7",
    "border": "#d5c9b3",
    "text": "#21302c",
    "muted": "#63756d",
    "accent": "#5f806f",
    "accent_dark": "#486457",
    "danger": "#8a5341",
    "overlay": "#000000",
    "device_outer": "#d7d0c5",
    "device_inner": "#f2eee8",
}

VOLUMES_ROOT = Path("/Volumes")
