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
| `gap_schema.py` | Scout file has 15+ recent sourced complaints across 3+ apps, keyword popularity, no excluded category | Yes |
| `spec_gate.py` | Spec front matter, sections, under 600 words, 5 scout-sourced competitors, 3 complaints from 3 apps, capability differentiator | Yes |
| `demand_assets.py` | Landing page has the three events, matching price, privacy link, email and consent, no payment form, clean copy; 1 to 3 ads | Yes |
| `overlap.py` | Feature code outside the shared scaffold overlaps no earlier app above the cap | Yes |
| `review_checklist.py` | Every App Review row passes with evidence on disk and is verified; no template row missing | Yes |
| `content_lint.py` | Captions pass copy lint, hashtag cap, label fields present, no AI label while realistic AI is disabled | Yes |

Run the tests from the repo root: `python -m pytest -q`.
