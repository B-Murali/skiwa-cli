"""Home-screen banner: picks the widest bundled ANSI art that still fits the
current terminal, so it doesn't wrap into garbled output on narrow windows.
"""
from __future__ import annotations

import shutil

from .config import ASSETS

# (min terminal columns, asset file), widest first.
BANNERS = [
    (160, ASSETS / "banner_160.ans"),
    (140, ASSETS / "banner_140.ans"),
    (120, ASSETS / "banner_120.ans"),
    (100, ASSETS / "banner_100.ans"),
    (80, ASSETS / "banner_80.ans"),
    (48, ASSETS / "banner_48.ans"),
]


def print_banner() -> None:
    columns = shutil.get_terminal_size().columns
    for min_width, path in BANNERS:
        if columns >= min_width and path.exists():
            print(path.read_text())
            return
    # Terminal narrower than every banner we have — skip rather than wrap it.
