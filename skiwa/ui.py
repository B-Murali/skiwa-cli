"""Home-screen banner: picks the widest bundled ANSI art that still fits the
current terminal, so it doesn't wrap into garbled output on narrow windows.
"""
from __future__ import annotations

import shutil
import sys

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


def _enable_windows_ansi() -> None:
    """Classic cmd.exe/PowerShell consoles ignore ANSI escapes unless VT
    processing is turned on for the current session; Windows Terminal (and
    anything already VT-aware) is unaffected. No-op on non-Windows.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass  # Best-effort only — worst case the banner shows raw escapes.


def print_banner() -> None:
    _enable_windows_ansi()
    columns = shutil.get_terminal_size().columns
    for min_width, path in BANNERS:
        if columns >= min_width and path.exists():
            print(path.read_text(encoding="utf-8"))
            return
    # Terminal narrower than every banner we have — skip rather than wrap it.
