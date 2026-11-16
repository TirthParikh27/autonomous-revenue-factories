#!/usr/bin/env python3
"""Static checks on one demand-test landing page and its ads (skills/demand-test).

    demand_assets.py SITE_DIR --price N [--claims CLAIMS.yaml]

SITE_DIR is demand/<id>/site/ with index.html (and any .js files). Ads are the .txt and .md files in
the sibling folder demand/<id>/ads/. Claims default to demand/<id>/claims.yaml when it exists.
Exit 1 unless: the events page_view, price_click and committed_signup appear in the HTML or JS; every
dollar price on the page equals --price and at least one is shown; a privacy link exists (a relative
one must point at a file in SITE_DIR); there is an email input and a consent line; there is no payment
form (card or CVC inputs, cc- autocomplete, a password field, or anything mentioning stripe); copy lint
passes on the page's visible text (pre-build, with price) and on each ad (pre-build); and there are
1 to ads.max_creatives_per_idea ad files.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import yaml

import copy_lint
from _common import load_budget

EVENTS = ("page_view", "price_click", "committed_signup")
AD_SUFFIXES = {".txt", ".md"}
PAYMENT_PATTERNS = [
    (r"<input[^>]*\b(name|id|autocomplete)\s*=\s*['\"][^'\"]*(card|cc-|cvc|cvv|expiry)[^'\"]*['\"]", "card input"),
    (r"<input[^>]*\btype\s*=\s*['\"]?password", "password input"),
    (r"stripe", "stripe reference"),
]


def visible_text(page: str) -> str:
    page = re.sub(r"<(script|style|noscript)\b.*?</\1\s*>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<!--.*?-->", " ", page, flags=re.S)
    page = re.sub(r"<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page)).strip()


def page_problems(site: Path, price: float, claims: list[str]) -> list[str]:
    index = site / "index.html"
    if not index.is_file():
        return [f"no index.html in {site}"]
    page = index.read_text()
    code = page + "\n" + "\n".join(p.read_text() for p in sorted(site.rglob("*.js")))
    low = code.lower()
    out = [f"event '{e}' not found in page or scripts" for e in EVENTS if e not in code]

    text = visible_text(page)
    shown = [float(p) for p in re.findall(r"\$\s?(\d+(?:\.\d{1,2})?)", text)]
    if not shown:
        out.append("no price shown on the page")
    for value in shown:
        if abs(value - price) > 0.001:
            out.append(f"page shows ${value:g}, spec price is ${price:g}")

    links = re.findall(r"href\s*=\s*['\"]([^'\"]*privacy[^'\"]*)['\"]", page, re.I)
    if not links:
        out.append("no privacy link")
    for link in links:
        if not re.match(r"(https?:|mailto:|#)", link, re.I):
            target = site / link.split("#")[0].split("?")[0].lstrip("/")
            if not target.is_file():
                out.append(f"privacy link '{link}' does not resolve to a file in the site")

    if not re.search(r"<input[^>]*\btype\s*=\s*['\"]?email", page, re.I):
        out.append("no email input")
    if not re.search(r"\bconsent\b|\bi agree\b|\bagree to\b", text, re.I):
        out.append("no consent line")
    for pattern, label in PAYMENT_PATTERNS:
        hit = re.search(pattern, low, re.I)
        if hit:
            out.append(f"payment form not allowed ({label}): '{hit.group(0)[:60]}'")

    out += [f"page copy: {p}" for p in copy_lint.lint(text, pre_build=True, has_price=True, claims=claims)]
    return out


def ad_problems(ads_dir: Path, max_ads: int, claims: list[str]) -> list[str]:
    files = sorted(p for p in ads_dir.glob("*") if p.is_file() and p.suffix.lower() in AD_SUFFIXES) \
        if ads_dir.is_dir() else []
    out = []
    if not 1 <= len(files) <= max_ads:
        out.append(f"{len(files)} ad file(s) in {ads_dir}, need 1 to {max_ads}")
    for path in files:
        out += [f"ad {path.name}: {p}" for p in copy_lint.lint(path.read_text(), pre_build=True, claims=claims)]
    return out


def load_claims(path: Path | None) -> list[str]:
    if not path or not path.is_file():
        return []
    loaded = yaml.safe_load(path.read_text()) or {}
    return [c if isinstance(c, str) else str(c.get("claim", "")) for c in loaded.get("claims", [])]


def problems(site: Path, price: float, max_ads: int, claims: list[str] | None = None) -> list[str]:
    return page_problems(site, price, claims or []) + ad_problems(site.parent / "ads", max_ads, claims or [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    parser.add_argument("--price", type=float, required=True)
    parser.add_argument("--claims", type=Path)
    args = parser.parse_args(argv)
    max_ads = int(load_budget()["ads"]["max_creatives_per_idea"])
    claims = load_claims(args.claims or args.site.parent / "claims.yaml")
    found = problems(args.site, args.price, max_ads, claims)
    for line in found:
        print(f"FAIL demand_assets: {line}")
    if not found:
        print(f"OK demand_assets: {args.site} at ${args.price:g}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
