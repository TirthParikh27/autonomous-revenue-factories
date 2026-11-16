# Factory A checks

Scripts that decide, so the model does not. Each exits non-zero on a fail and prints the reason. Thresholds come from `../budget.yaml`.

| Script | Gate | Built |
|---|---|---|
| `screen_rank.py` | Turns three LLM rankings into kills. Bottom half by median rank | Yes |
| `copy_lint.py` | No testimonials, ratings, counts or "available now" on pages and ads | Yes |
| `portfolio_distinct.py` | A new idea is not a copy of one already in the pipeline | Yes |
| `ads_paused.py` | Ad plans stay under budget. Campaigns read back paused | Yes |
| `decide.py` | Kill, advance and winner rules for both ad tests | Yes |
| `cadence.py` | Store release pace, live app cap, freeze on a spam or fraud citation | Yes |
| `metadata_similarity.py` | Listings are not templates of each other | Yes |
| `gap_schema`, `spec_gate`, `demand_assets`, `overlap`, `review_checklist`, `content_lint` | Named in the skills | Not yet |

Run the tests from the repo root: `python -m pytest -q`.
