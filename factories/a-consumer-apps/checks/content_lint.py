#!/usr/bin/env python3
"""Content draft lint (skills/content-drafts step 6).

    content_lint.py MANIFEST.json|BATCH_DIR [--claims CLAIMS.yaml]

Manifest: {"posts": [{"format", "caption", "hashtags": [...], "concept": bool,
                      "ai_generated_elements": [...], "ai_label_required": bool, ...}]}
A directory argument reads its manifest.json. Per post, exit 1 if: copy_lint fails on the caption
(concept posts are linted as pre-build copy, so they must say "in development" or "early access");
there are more than content.max_hashtags distinct hashtags across the `hashtags` field and the
caption; `concept`, `ai_generated_elements` or `ai_label_required` is missing; or `ai_label_required`
is true while content.allow_realistic_ai_people_or_scenes is false.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import copy_lint
from _common import load_budget
from demand_assets import load_claims

LABEL_FIELDS = ("concept", "ai_generated_elements", "ai_label_required")
HASHTAG = re.compile(r"#([a-z_][a-z0-9_]*)", re.I)


def hashtags(post: dict) -> set[str]:
    tags = {str(t).lstrip("#").lower() for t in post.get("hashtags") or []}
    return tags | {t.lower() for t in HASHTAG.findall(str(post.get("caption") or ""))}


def problems(manifest: dict | list, rules: dict, claims: list[str] | None = None) -> list[str]:
    posts = manifest.get("posts", []) if isinstance(manifest, dict) else manifest
    out = [] if posts else ["manifest has no posts"]
    for i, post in enumerate(posts):
        label = f"post {post.get('id', i)}"
        for field in LABEL_FIELDS:
            if post.get(field) is None:
                out.append(f"{label}: missing {field}")
        caption = str(post.get("caption") or "")
        if not caption.strip():
            out.append(f"{label}: missing caption")
        for p in copy_lint.lint(caption, pre_build=post.get("concept") is True, claims=claims or []):
            out.append(f"{label}: {p}")
        tags = hashtags(post)
        if len(tags) > rules["max_hashtags"]:
            out.append(f"{label}: {len(tags)} hashtags, limit {rules['max_hashtags']}")
        if post.get("ai_label_required") is True and not rules.get("allow_realistic_ai_people_or_scenes"):
            out.append(f"{label}: needs an AI label, but realistic AI people or scenes are disabled in budget.yaml")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--claims", type=Path)
    args = parser.parse_args(argv)
    path = args.manifest / "manifest.json" if args.manifest.is_dir() else args.manifest
    manifest = json.loads(path.read_text())
    found = problems(manifest, load_budget()["content"], load_claims(args.claims))
    for line in found:
        print(f"FAIL content_lint: {line}")
    if not found:
        print(f"OK content_lint: {path} clean")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
