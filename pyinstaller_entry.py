"""PyInstaller entry point. Not a package module — PyInstaller needs a
top-level script to build from; `skiwa.cli:main` (the console_scripts entry)
isn't directly usable as a build target.
"""
import sys

from skiwa.cli import main

if __name__ == "__main__":
    sys.exit(main())
