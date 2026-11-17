"""Reads every factory's files and returns one plain dict for the UI pages.

Reads only what factories/_shared/CONVENTIONS.md defines: item files, open escalation packets,
the spend ledger, the outbox, budget.yaml and STOP files. It writes nothing.
Months are UTC months, the same rule the run wrapper uses for its budget check.
"""
import datetime as dt
import json
import re
from pathlib import Path

import yaml

CONFIG = Path(__file__).with_name("factories.yaml")
PARKED = {"killed", "awaiting_human"}          # stages that say what happened to an item, not where it got to
RUN_ID = re.compile(r"\d{8}T\d{6}Z-(.+)-[0-9a-f]{6}")


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except ValueError as err:
        raise ValueError(f"{path}: {err}") from err


def read_item(path: Path) -> dict:
    """An item file, checked for the fields the pages rely on, so a bad one is named instead of half-drawn."""
    item = read_json(path)
    if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ("id", "stage")):
        raise ValueError(f"{path}: an item needs an id and a stage")
    if not isinstance(item.get("history") or [], list) or not isinstance(item.get("blocked_by") or "", str):
        raise ValueError(f"{path}: history must be a list and blocked_by a path")
    if not isinstance(item.get("spend_usd", 0), (int, float)):
        raise ValueError(f"{path}: spend_usd must be a number")
    return item


def read_caps(path: Path) -> dict:
    """budget.yaml's monthly dollar caps. Other settings kept beside them, such as warn_at_fraction, are not caps."""
    if not path.exists():
        return {}
    try:
        caps = (yaml.safe_load(path.read_text()) or {}).get("monthly_caps_usd") or {}
        return {kind: float(cap) for kind, cap in caps.items() if not kind.endswith("_fraction")}
    except (yaml.YAMLError, AttributeError, TypeError, ValueError) as err:
        raise ValueError(f"{path}: {err}") from err


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except ValueError as err:
        raise ValueError(f"{path}: {err}") from err


def local(at: str) -> dt.datetime:
    return dt.datetime.fromisoformat(at.replace("Z", "+00:00")).astimezone()


def clock(at: str) -> str:
    """'8:44 pm' in the reader's own time zone."""
    return local(at).strftime("%I:%M %p").lstrip("0").lower()


def title(slug: str) -> str:
    words = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug).replace("-", " ").replace("_", " ")
    return words[:1].upper() + words[1:]


def skill_of(run: str | None) -> str | None:
    match = RUN_ID.fullmatch(run or "")
    return match.group(1) if match else None


def reached(item: dict) -> list[str]:
    """Every real stage the item has been in, oldest first."""
    stages = [step["to"] for step in item.get("history") or [] if step.get("to") not in PARKED]
    if item["stage"] not in PARKED and item["stage"] not in stages:
        stages.append(item["stage"])
    return stages


def columns(configured: list[dict], items: list[dict]) -> list[dict]:
    """The configured stage columns, plus one for any stage an item reached that no column holds."""
    cols = [{"runs": [], **col} for col in configured]
    held = {stage for col in cols for stage in col["from"]}
    for item in items:
        for stage in reached(item):
            if stage not in held:
                held.add(stage)
                cols.append({"id": stage, "name": title(stage), "from": [stage], "runs": []})
    return cols


def read_packet(path: Path) -> dict:
    """An escalation packet: its heading, its header line and the first paragraph of what is asked."""
    text = path.read_text()
    heading = re.search(r"^# (.+)$", text, re.M)
    field = lambda name: (re.search(rf"\b{name}: *(.+?)(?=   |\n|$)", text) or [None, None])[1]  # noqa: E731
    asked = re.search(r"^## What I want to do\s*\n(.+?)(?=\n\s*\n|\n\||\Z)", text, re.M | re.S)
    return {
        # the rule that raised it: its header says so, else the file name starts with it (BUD-1-20261117-...)
        "trigger": field("Trigger") or re.sub(r"-\d{8}-.*", "", path.stem),
        "title": heading.group(1).strip() if heading else title(path.stem),
        "detail": " ".join(asked.group(1).split())[:400] if asked else "",
        "expires": field("Expires"),
    }


def paper_line(folder: Path, item_id: str) -> list[float] | None:
    """A strategy's paper result so far, in percent, one point per day (c-trading's paper/<id>.json)."""
    path = folder / "paper" / f"{item_id}.json"
    if not path.exists():
        return None
    total, line = 1.0, [0.0]
    for _day, result, *_ in read_json(path).get("daily", []):
        total *= 1 + result
        line.append(round((total - 1) * 100, 2))
    return line


def factory(folder: Path, root: Path, shown: dict, now: dt.datetime) -> dict:
    items = [read_item(path) for path in sorted((folder / "state" / "items").glob("*.json"))]
    cols = columns(shown.get("stages", []), items)
    col_of_stage = {stage: col["id"] for col in cols for stage in col["from"]}
    col_of_skill = {skill: col["id"] for col in cols for skill in col["runs"]}
    ledger = read_jsonl(folder / "ledger" / "spend.jsonl")
    outbox = read_jsonl(folder / "outbox" / "pending.jsonl")
    caps = read_caps(folder / "budget.yaml")

    approvals, seen = {}, {}
    for path in sorted((folder / "escalations" / "open").glob("*.md")):
        packet = read_packet(path)
        trigger = packet.pop("trigger")
        seen[trigger] = seen.get(trigger, 0) + 1
        # the run that raised a packet is named in its file name
        skill = max((skill for skill in col_of_skill if skill in path.stem), key=len, default=None)
        approvals[path.name] = {
            **packet, "id": trigger + (f" ({seen[trigger]})" if seen[trigger] > 1 else ""),
            "stage": col_of_skill.get(skill), "file": path.relative_to(root).as_posix(), "items": [],
        }

    shown_items = []
    for col in cols:
        col["reached"] = 0
    for item in items:
        stages = reached(item)
        for col in cols:
            col["reached"] += bool(set(stages) & set(col["from"]))
        packet = approvals.get(Path(item.get("blocked_by") or "").name)
        killed = item["stage"] == "killed"
        waiting = item["stage"] == "awaiting_human"
        history = item.get("history") or []
        scores = item.get("scores") or {}
        # an item that is waiting or killed sits at the stage whose run parked it there
        parked_by = next((skill_of(step.get("run")) for step in reversed(history) if step.get("to") == item["stage"]), None)
        stage = ((waiting or killed) and col_of_skill.get(parked_by)) or (col_of_stage[stages[-1]] if stages else None)
        if packet:
            packet["items"].append(item["id"])
            packet["stage"] = packet["stage"] or stage
        shown_items.append({
            "id": item["id"],
            "name": title(item["id"]),
            "stage": stage,
            "state": "killed" if killed else "waiting" if waiting else "running",
            "summary": item.get("summary", ""),
            "category": item.get("category"),
            "platform": item.get("platform"),
            "facts": {key: value for key, value in scores.items() if isinstance(value, (int, float)) and not isinstance(value, bool)},
            "evidence": [{"claim": e.get("claim", ""), "source": e.get("source", "")} for e in item.get("evidence", [])],
            "spend": item.get("spend_usd", 0),
            "blockedBy": packet["id"] if packet else None,
            "killed": (item.get("killed_reason") or (history[-1].get("note") if history else "") or "No reason recorded") if killed else None,
            "history": [[clock(step["at"]), title(step.get("to") or ""), step.get("note", "")] for step in history],
            "pnl": paper_line(folder, item["id"]),
        })

    month = now.astimezone(dt.timezone.utc).strftime("%Y-%m")
    spent, runs, cost_of_run = {}, set(), {}
    for line in ledger:
        if line.get("run"):
            cost_of_run[line["run"]] = cost_of_run.get(line["run"], 0) + line["usd"]
        if line["at"].startswith(month):
            category = line.get("category", "other")
            spent[category] = spent.get(category, 0) + line["usd"]
            runs.add(line.get("run"))
    events = []
    for line in outbox:
        skill = skill_of(line.get("run"))
        events.append({
            "at": line["at"], "t": clock(line["at"]), "stage": col_of_skill.get(skill), "skill": skill or "wrapper",
            "text": line["text"], "cost": round(cost_of_run.get(line.get("run"), 0), 2), "failed": " failed" in line["text"],
        })
    events.sort(key=lambda event: local(event["at"]), reverse=True)
    for col in cols:
        last = next((event for event in events if event["stage"] == col["id"]), None)
        col["last"] = last and {"t": last["t"], "text": last["text"]}
        del col["from"]

    stops = [path for path in (root / "STOP", folder / "STOP", folder / "state" / "STOP") if path.exists()]
    return {
        "id": folder.name,
        "name": shown.get("name", title(folder.name)),
        "short": shown.get("short", title(folder.name)),
        "tagline": shown.get("tagline", ""),
        "planned": not items and not outbox,
        "on": not stops,
        # each STOP file that holds this factory off, with what it says
        "stopped_by": [{"file": path.relative_to(root).as_posix(), "why": path.read_text().strip()[:300]} for path in stops],
        "stages": cols,
        "items": shown_items,
        "approvals": list(approvals.values()),
        "events": events[:40],
        "spend": {
            "month": round(sum(spent.values()), 2), "monthBudget": caps.get("total", 0), "runs": len(runs - {None}),
            # one line per capped kind of spend, so a factory shows the caps it has and no others
            "caps": [{"kind": kind, "spent": round(spent.get(kind, 0), 2), "cap": cap} for kind, cap in caps.items() if kind != "total"],
        },
    }


def read_factory(folder: Path, root: Path, shown: dict, now: dt.datetime) -> dict:
    """factory(), with any file of the wrong shape reported as a ValueError that names the factory."""
    try:
        return factory(folder, root, shown, now)
    except (KeyError, TypeError, AttributeError) as err:
        raise ValueError(f"{folder}: a file has the wrong shape ({type(err).__name__}: {err})") from err


def build(root: Path, now: dt.datetime | None = None) -> dict:
    """Everything the pages show, for the factories under root/factories."""
    now = now or dt.datetime.now().astimezone()
    shown = yaml.safe_load(CONFIG.read_text())
    folders = [
        path for path in sorted((root / "factories").glob("*/"))
        if not path.name.startswith(("_", ".")) and not shown.get(path.name, {}).get("hidden")
    ]
    return {
        "asOf": now.strftime("%d %b %Y, %I:%M %p").lstrip("0"),
        "factories": [read_factory(folder, root, shown.get(folder.name, {}), now) for folder in folders],
    }
