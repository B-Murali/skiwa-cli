#!/usr/bin/env python3
"""Verify a downloaded file's sha256 against a gh-style checksums.txt line.

Cross-platform on purpose: `sha256sum`/`shasum` availability differs across
the macOS/Linux/Windows runners this build matrix uses, but every runner has
the same Python we already need for PyInstaller.
"""
import hashlib
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: verify_checksum.py <downloaded-file> <checksums.txt>", file=sys.stderr)
        return 2
    archive = Path(sys.argv[1])
    checksums = Path(sys.argv[2])

    expected = None
    for line in checksums.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == archive.name:
            expected = parts[0]
            break
    if not expected:
        print(f"no checksum entry for {archive.name} in {checksums}", file=sys.stderr)
        return 1

    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        print(f"checksum mismatch for {archive.name}: got {actual}, expected {expected}", file=sys.stderr)
        return 1

    print(f"{archive.name}: checksum OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
