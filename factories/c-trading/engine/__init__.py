"""The judge. Agents may run and read this package. They may not edit it (F-ENG-1)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Installed libraries come before this folder on the import path, so a file an agent drops here
# (a `yaml.py`, say) cannot stand in for a library the judge imports.
sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd(), str(ROOT))] + [str(ROOT)]

import yaml  # noqa: E402
CONFIG = yaml.safe_load((Path(__file__).resolve().parent / "config.yaml").read_text())
GATE = yaml.safe_load((Path(__file__).resolve().parent / "gate.yaml").read_text())
