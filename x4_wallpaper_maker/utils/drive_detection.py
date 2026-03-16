"""Mounted volume detection for macOS-first export workflows."""

from __future__ import annotations

import plistlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from x4_wallpaper_maker.utils.constants import VOLUMES_ROOT


@dataclass(slots=True)
class DriveInfo:
    name: str
    path: Path
    is_removable: bool
    filesystem: str | None = None
    volume_name: str | None = None

    @property
    def label(self) -> str:
        suffix = "Removable" if self.is_removable else "Mounted"
        return f"{self.name} ({suffix})"


def _diskutil_info(path: Path) -> dict[str, object]:
    diskutil = shutil.which("diskutil")
    if not diskutil:
        return {}
    try:
        result = subprocess.run(
            [diskutil, "info", "-plist", str(path)],
            check=False,
            capture_output=True,
            timeout=1.5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if result.returncode != 0 or not result.stdout:
        return {}
    try:
        return plistlib.loads(result.stdout)
    except Exception:
        return {}


def list_mounted_volumes() -> list[DriveInfo]:
    """Return currently mounted top-level volumes without persisting history."""
    if not VOLUMES_ROOT.exists():
        return []

    drives: list[DriveInfo] = []
    for path in sorted((item for item in VOLUMES_ROOT.iterdir() if item.is_dir()), key=lambda item: item.name.lower()):
        info = _diskutil_info(path)
        removable = bool(info.get("RemovableMedia")) or bool(info.get("Ejectable"))
        filesystem = info.get("FilesystemName")
        volume_name = info.get("VolumeName")
        drives.append(
            DriveInfo(
                name=path.name,
                path=path,
                is_removable=removable,
                filesystem=str(filesystem) if filesystem else None,
                volume_name=str(volume_name) if volume_name else None,
            )
        )
    return drives

