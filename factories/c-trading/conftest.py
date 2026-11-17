import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# The repo-wide check job installs only pytest and pyyaml. These tests need the
# factory's own requirements and run in the c-trading workflow.
if importlib.util.find_spec("vectorbt") is None:
    collect_ignore_glob = ["tests/*"]
