#!/usr/bin/env python3
"""Listing similarity gate: a new listing must not read like a template of another on the account.

    metadata_similarity.py NEW_LISTING.json OTHER_LISTING.json...

Listing: {"name", "subtitle", "description", "keywords", "release_notes", "screenshot_captions": [..]}
Similarity is word-trigram overlap (Jaccard, percent) per text field. Unrelated prose scores near 0.
Exit 1 if any field against any other listing is over `max_listing_text_similarity_pct`, or a name matches.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import jaccard_pct, load_budget, shingles, words

LONG_FIELDS = ("description", "release_notes", "screenshot_captions")
SHORT_FIELDS = ("subtitle", "keywords")


def text_of(listing: dict, field: str) -> str:
    value = listing.get(field, "")
    return " ".join(value) if isinstance(value, list) else str(value or "")


def compare(new: dict, other: dict) -> dict[str, float]:
    scores = {f: jaccard_pct(shingles(text_of(new, f)), shingles(text_of(other, f))) for f in LONG_FIELDS}
    scores.update({f: jaccard_pct(set(words(text_of(new, f))), set(words(text_of(other, f)))) for f in SHORT_FIELDS})
    return scores


def problems(new: dict, others: dict[str, dict], limit: float) -> list[str]:
    out = []
    for label, other in others.items():
        if words(text_of(new, "name")) == words(text_of(other, "name")) and words(text_of(new, "name")):
            out.append(f"name is identical to {label}")
        for field, score in compare(new, other).items():
            # short fields share common words by nature, so they get twice the room
            allowed = limit * 2 if field in SHORT_FIELDS else limit
            if score > allowed:
                out.append(f"{field} is {score:.0f}% similar to {label} (limit {allowed:.0f}%)")
    return out


def main(argv: list[str]) -> int:
    limit = float(load_budget()["account_protection"]["max_listing_text_similarity_pct"])
    new = json.loads(Path(argv[1]).read_text())
    others = {p: json.loads(Path(p).read_text()) for p in argv[2:]}
    found = problems(new, others, limit)
    for line in found:
        print(f"FAIL metadata_similarity: {line}")
    if not found:
        print(f"OK metadata_similarity: compared with {len(others)} listing(s), limit {limit:.0f}%")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
