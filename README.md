# X4 Wallpaper Maker

Local-only desktop utility for turning user-supplied images into CrossPoint-compatible Xteink X4 sleep and wallpaper BMPs.

## Privacy position

This app is designed to minimize residual traces by default: local-only processing, no cloud, no analytics, no image cache, no recent file history, in-memory processing wherever practical, and deliberate clearing of internal state after export or session reset. Absolute forensic non-recoverability cannot be guaranteed on a general-purpose OS.

## Stack

- Python 3.12
- PySide6
- Pillow

## Quick start

```bash
./run-app.sh
```

The script handles first-run setup for you:

- picks Python 3.12
- creates or repairs `.venv`
- installs the app into that venv
- launches `x4-wallpaper-maker`

## Manual install

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/x4-wallpaper-maker
```

If you want the test tools too:

```bash
.venv/bin/python -m pip install -e '.[dev]'
```

## Test

```bash
.venv/bin/python -m pytest
```

## Features

- Import `jpg`, `jpeg`, `png`, `webp`, and `bmp`
- Fixed 3:5 portrait crop composition
- Preview in `Standard`, `Dithered`, and `Mono` modes
- Export as `sleep.bmp`, into `/.sleep`, into `/sleep`, or as a custom `.bmp`
- No telemetry, no network calls, no recent-file persistence, and no temp preview images
