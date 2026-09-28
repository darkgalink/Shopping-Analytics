"""Resource/output path helpers that work both from source and from a PyInstaller bundle."""

import os
import sys


def _base_dir():
    if getattr(sys, "frozen", False):
        # one-file bundles extract resources to sys._MEIPASS
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(*parts):
    return os.path.join(_base_dir(), *parts)


def output_path(*parts):
    """Writable path rooted at the current working directory (logs/CSV)."""
    path = os.path.join(os.getcwd(), *parts)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    return path


def ensure_output_dirs():
    os.makedirs(os.path.join(os.getcwd(), "data", "logs"), exist_ok=True)
