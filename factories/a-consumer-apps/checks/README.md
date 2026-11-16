# Factory A checks

Hard gates exist only where a mistake costs money, risks the store or ad account, or creates a legal problem. Everything else (which ideas to keep, when demand is proven, what counts as a winner) is decided by the run, which writes its reasoning and numbers in the run report.

| Script | Hard gate |
|---|---|
| `ads_paused.py` | Ad plans stay under the tranche and monthly budgets. Campaigns read back paused |
| `cadence.py` | Store release pace, live app cap, freeze after a spam or fraud citation |
| `copy_lint.py` | No testimonials, ratings, user counts or "available now" on pre-build pages and ads |
| `metadata_similarity.py` | Store listings on the account are not templates of each other |
| `overlap.py` | Feature code is not a copy of an earlier app |

Limits come from `../budget.yaml`. Each script exits non-zero on a fail and prints the reason.

Tests cover these gates and nothing else. Run them from the repo root: `python -m pytest -q`.
