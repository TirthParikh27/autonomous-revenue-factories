#!/usr/bin/env python3
"""The only step that may write to an ad or social account. It replaces the publisher agents.

    publish.py ads PLAN.json --packet A-AD-1      campaigns, always created PAUSED
    publish.py drafts MANIFEST.json               social posts, always created as drafts

Dry run is the only mode built so far. It makes no network call and spends nothing: it writes
readback.json (ads) or drafts.json (posts) next to the input, shaped like a real read-back, so
every later step can be exercised before any account exists. Live mode is added when the
operator supplies Meta and Postiz credentials, and must keep the same checks and outputs.

Both commands refuse on a STOP file, skip anything already written (so a retry cannot
duplicate), and exit non-zero with the reason on any problem.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(FACTORY_DIR / "checks"))
import ads_paused  # noqa: E402
import copy_lint  # noqa: E402
from _common import load_budget, read_jsonl  # noqa: E402


def stopped(state_dir: Path) -> bool:
    return any((d / "STOP").exists() for d in (state_dir, FACTORY_DIR, FACTORY_DIR.parent.parent))


def publish_ads(plan_path: Path, packet: str, state_dir: Path, budget: dict, month: str) -> list[str]:
    """Create the plan's campaigns paused. Returns problems; empty means done."""
    if not any(packet in p.name for p in (state_dir / "escalations" / "approved").glob("*")):
        return [f"no approved packet matching '{packet}' in escalations/approved/"]
    plan = json.loads(plan_path.read_text())
    spent = sum(float(l.get("usd", 0)) for l in read_jsonl(state_dir / "ledger" / "spend.jsonl")
                if l.get("category") == "ads" and str(l.get("at", "")).startswith(month))
    problems = ads_paused.check_plan(plan, budget, spent)
    if problems:
        return problems
    out = plan_path.with_name("readback.json")
    existing = json.loads(out.read_text())["campaigns"] if out.exists() else []
    have = {c["ref"] for c in existing}
    for c in plan["campaigns"]:
        if c["ref"] not in have:
            existing.append({"ref": c["ref"], "id": f"dry-{c['ref']}", "status": "PAUSED",
                             "lifetime_budget_usd": c["lifetime_budget_usd"], "days": c["days"]})
    out.write_text(json.dumps({"dry_run": True, "packet": packet, "campaigns": existing}, indent=2) + "\n")
    return ads_paused.check_readback(plan, {"campaigns": existing})


def publish_drafts(manifest_path: Path, claims: list[str]) -> list[str]:
    """Create the manifest's posts as drafts. Returns problems; empty means done."""
    posts = json.loads(manifest_path.read_text()).get("posts", [])
    problems = [] if posts else ["manifest has no posts"]
    for n, post in enumerate(posts, 1):
        if not post.get("caption"):
            problems.append(f"post {n}: no caption")
        if post.get("ai_label_required"):
            problems.append(f"post {n}: needs an AI label, which is an A-CNT-1 decision")
        for asset in post.get("assets", []):
            if not (manifest_path.parent / asset).exists():
                problems.append(f"post {n}: asset {asset} does not exist")
        text = " ".join([post.get("caption", ""), *post.get("hashtags", [])])
        problems += [f"post {n}: {p}" for p in copy_lint.lint(text, claims=claims)]
    if problems:
        return problems
    out = manifest_path.with_name("drafts.json")
    existing = json.loads(out.read_text())["drafts"] if out.exists() else []
    for n in range(len(existing) + 1, len(posts) + 1):
        existing.append({"post": n, "id": f"dry-{n}", "state": "draft"})
    out.write_text(json.dumps({"dry_run": True, "drafts": existing}, indent=2) + "\n")
    return []


def main(argv: list[str] | None = None) -> int:
    import datetime as dt
    import yaml
    parser = argparse.ArgumentParser(description="Publisher step (dry run only for now).")
    parser.add_argument("kind", choices=["ads", "drafts"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--packet", help="ads: id of the approved packet, for example A-AD-1")
    parser.add_argument("--claims", type=Path, help="drafts: the item's claims.yaml")
    parser.add_argument("--state-root", type=Path, default=FACTORY_DIR)
    args = parser.parse_args(argv)
    if stopped(args.state_root):
        problems = ["STOP file present"]
    elif args.kind == "ads":
        if not args.packet:
            parser.error("ads needs --packet")
        problems = publish_ads(args.path, args.packet, args.state_root, load_budget(),
                               dt.date.today().strftime("%Y-%m"))
    else:
        claims = (yaml.safe_load(args.claims.read_text()) or {}).get("claims", []) if args.claims else []
        problems = publish_drafts(args.path, [c if isinstance(c, str) else str(c.get("claim", "")) for c in claims])
    for p in problems:
        print(f"FAIL publish {args.kind}: {p}")
    if not problems:
        print(f"OK publish {args.kind}: dry run, nothing left this machine. See {args.path.parent}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
