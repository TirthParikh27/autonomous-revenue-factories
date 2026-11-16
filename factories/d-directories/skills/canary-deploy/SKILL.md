---
name: canary-deploy
description: Prepare the production deploy pull request and approval packet for a site's canary of at most 40 pages, or for a later approved page tier, and confirm afterwards that the pages are really served. Use when an item is at qa_passed, or when a D-PUB-1 or D-SCALE-1 packet has been approved and merged.
---

# Canary deploy

You are running stage 6 of Factory D as the publisher. Assume no prior context. Read `CLAUDE.md` and `budget.yaml` (sections `indexing`, `per_run.canary_deploy`) first.

You never deploy. You prepare a pull request. The operator's merge to `main` triggers the production deploy. The deploy mechanism (Cloudflare Pages building from `main`, or a CI deploy job) is set up at build time and its credentials are not in your environment.

## Mode A: prepare the canary (item at `qa_passed`)

1. Confirm `sites/<id>/qa_report.json` is a pass for the current commit. If the site changed since QA, stop and send it back to `content-qa`.
2. Select the canary set: at most `indexing.canary_pages` pages. Take the listing pages with the highest verified attribute count, plus the home page, sources, removal and disclosure pages, plus only those category pages whose listings are all inside the set. Record the list in `sites/<id>/canary_set.json`.
3. Configure the build so only the canary set is generated and listed in the sitemap. Pages outside the set are not built.
4. Rebuild and re-run `tools/check_build` and the three content QA scripts on the canary build. All must pass.
5. Open a pull request to `main` from the `claude/` branch. The description lists the canary URLs, the check outputs and the preview URL if one exists.
6. Raise `D-PUB-1` with the `escalate` skill. Include everything `ESCALATION.md` requires. List the operator steps: merge the pull request; point the purchased domain at the site; verify the Search Console property; submit the sitemap; add the analytics property. You do none of these.
7. The item moves to `awaiting_human`. End with the `run-report` skill.

## Mode B: confirm the outcome (packet approved and pull request merged)

1. Confirm the packet is in `escalations/approved/` and the pull request is merged. If only one is true, stop and report. Both are required.
2. Fetch every URL in the approved set on the production domain. Record status, final URL after redirects, the title, and the canonical link.
3. Fetch the live sitemap and the robots file.
4. Run `tools/check_live sites/<id>/` over the recorded fetch results.
5. On pass, set `canary_started` to today (Mode A canary) or record the tier start date (later tier), set `pages_live` and `page_cap`, and move the item to `canary_live` or `scaled`.
6. On failure, do not change the stage. Report exactly which URLs failed. Do not attempt a fix by pushing to `main`. Open a fix pull request or report that the deploy configuration needs the operator.
7. End with the `run-report` skill.

## Mode C: prepare a later tier (item at `index_confirmed` or `scaled`, scale gate passed)

1. Confirm `tools/eval_gates` reports the scale gate passed in the latest `state/metrics/<id>/` file. If not, exit.
2. The next tier is the next value in `indexing.page_tiers`. Never skip a tier. Never exceed `max_pages_per_site`.
3. Have `site-build` produce the tier build and `content-qa` pass it. This skill does not build.
4. Open the pull request and raise `D-SCALE-1`. Then Mode B applies after approval.

## Tools

- git and the GitHub connector for the pull request.
- HTTP fetch of the site's own production URLs only.
- `tools/check_build`, the content QA scripts, `tools/check_live`.
- Shared skills: `escalate`, `run-report`.

## Deterministic check

`tools/check_live` exits 0 only if: every URL in the approved set returns 200 on the approved domain with the expected title and a self-referencing canonical; the live sitemap lists exactly the approved set of indexable URLs and no others; the robots file does not block the set; a request for a URL outside the set returns 404; no page carries a noindex directive unless the manifest says it should. Paste its output line. A successful merge or a green deploy status is not this check.

## Outputs

- `sites/<id>/canary_set.json`, the pull request, the `D-PUB-1` or `D-SCALE-1` packet.
- Item at `awaiting_human`, then `canary_live` or `scaled` after Mode B.

## Stop conditions

- QA is stale, or any check fails on the canary build.
- The approved packet lists a different URL set from the merged pull request: stop and raise `GEN-1`.
- A `D-SPAM-1` or `D-LEGAL-1` packet is open for any site: no deploy preparation for any site.

## Never

- Never push to `main`, trigger a production deploy, change DNS or touch the hosting dashboard.
- Never submit a sitemap or a URL to Google, and never use any indexing submission service. The operator submits the sitemap once.
- Never include more pages than the approved tier, and never grow a tier inside an open pull request after the packet was written.
- Never set `canary_started` before `tools/check_live` passes. The indexing clock must start from pages that are really served.
- Never treat a Slack reply as the approval. Look for the packet in `approved/` and the merge.
