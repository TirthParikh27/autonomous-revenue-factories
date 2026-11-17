"""The judge. Agents may run and read this package. They may not edit it (F-ENG-1)."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((Path(__file__).resolve().parent / "config.yaml").read_text())
GATE = yaml.safe_load((Path(__file__).resolve().parent / "gate.yaml").read_text())
