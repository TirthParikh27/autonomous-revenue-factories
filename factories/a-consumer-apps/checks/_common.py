"""Shared helpers for Factory A's deterministic checks. No model is involved in any of them."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

FACTORY_DIR = Path(__file__).resolve().parent.parent


def load_budget(path: Path | None = None) -> dict:
    return yaml.safe_load((path or FACTORY_DIR / "budget.yaml").read_text())


def read_jsonl(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def shingles(text: str, n: int = 3) -> set[tuple[str, ...]]:
    w = words(text)
    if len(w) < n:
        return {tuple(w)} if w else set()
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def jaccard_pct(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return 100.0 * len(a & b) / len(a | b)
