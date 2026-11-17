---
name: spec-differentiation
description: Stage 3 of Factory A. Use when items sit at `screened` to write a one-page spec with a differentiation statement and judge whether it is distinct, moving the item to `specced` or `killed`. Not for building anything.
---

# Spec and differentiation gate

You are a fresh session. Read `CLAUDE.md` and `budget.yaml` first. You work only from the validated scout file. You do not browse.

## Inputs

- Items at `screened` in `state/items/`, up to 10 a run. Each spec also states one proposed monthly price, taken from the price range of the named competitors, because the demand test shows it.
- Each item's `state/scout/<id>.json`.
- `state/specs/` for every earlier item, including killed ones.
- `data/spec_template.md`.

## Steps

1. For each item, write `state/specs/<id>.md` from the template. It is one short page with these sections:
   - **Job:** the single job the app does, for whom, in one sentence.
   - **Differentiation statement:** "Unlike <named competitors>, this app <capability>, which matters because <sourced complaint pattern>."
   - **Competitor table:** the nearest named apps with store URLs taken from the scout file, and what each lacks.
   - **Core features:** at most 3, each tied to the job.
   - **Not building:** what is deliberately left out.
   - **Monetisation:** hard paywall after onboarding that shows the core job working, trial length, intended price points marked as intentions.
   - **Target market:** note that median payer value is higher in North America than elsewhere in the RevenueCat data.
   - **Demand test plan:** the page promise and 6 concept post angles.
   - **Review risk:** which guideline areas this app is most exposed to.
   - **Claims:** the product claims content may make, each to be evidenced by the build later.
2. Check the spec: every competitor URL is in the scout file, the differentiation rests on sourced complaints from several competitors, the category is not excluded, and the core job, category and working name do not match any earlier item at `specced` or later.
3. If it holds up, have the `release-verifier` agent answer three questions from the spec and scout file only: could a reviewer tell this app from the 5 nearest competitors in one minute of use, is the differentiator a capability rather than a look or a price, and does any core feature depend on something the stack cannot do. It reports only gaps that affect correctness.
4. If both hold up: move the item to `specced`. Record the verifier's answers in `scores`.
5. Otherwise revise once. If it still falls short, move the item to `killed` with the reason.

## Tools

Read, Write, Edit, the two sub-agents. No web tools.

## Outputs

- `state/specs/<id>.md`.
- Item at `specced` or `killed`, with history appended.

## Stop conditions

- Per-item spend above `per_item_caps_usd.specced`: kill the item.
- The scout file is missing or quarantined: skip the item and report it.
- The spec would need a capability with legal weight (health, finance, children, user-generated content): raise `LEGAL-1`.

## Never

- Never pad the competitor table with apps the scout did not source.
- Never write a differentiator that is a colour scheme, a mascot, a lower price or "powered by AI".
- Never reuse the Job of a previous app, live or killed.
- Never promise a feature in the spec that needs a credential, data source or account the factory does not have.
- Never start any landing page, design or code in this stage.

## Finish

End by calling the shared `run-report` skill. Include your reasoning and the verifier's three answers for each item.
