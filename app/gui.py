"""Compatibility launcher for the GUI package.

Preferred command:
    python -m app.gui
"""

import sys

from app.gui.app_window import run_app


if __name__ == "__main__":
    sys.exit(run_app())