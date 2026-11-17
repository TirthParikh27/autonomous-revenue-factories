# Approve the first early-access email list and its privacy notice
Factory: a-consumer-apps   Item: batch 2026-11-17-b1   Trigger: PII-1   Raised: 2026-11-17   Expires: 2026-11-24

## What I want to do
Let the three demand-test pages collect an email address and a consent timestamp on a fake-door form. No page is deployed and nothing is collected until you approve.

## Why now (evidence)
Tranche 2 measures "price click followed by an email". Files: `demand/<id>/site/index.html` (form) and `site/privacy.html`.

## Details
- Fields: email address, consent timestamp, idea id. Nothing else.
- Stored: a Supabase early-access table (not yet created; `ACC-1`). Not readable by build or content runs. Telemetry reads counts only.
- Retention: not decided. Proposed: delete a list when its idea is killed, and all lists 90 days after the test ends.
- No email is ever sent (`emails_to_early_access_list: disabled`). If that changes: Spam Act 2003 duties (consent, sender identification, working unsubscribe; verified 2026-11-16).
- The Australian privacy position has not been researched.
- Privacy notice text: a short DRAFT is in each `site/privacy.html`. No `data/privacy_notice.md` exists, so I wrote it as a placeholder. Please supply or approve the text.

## Cost and worst case
No cost. Worst case: a notice that does not match the law, on a live page collecting emails.

## How to undo it
Delete the table rows and take the pages down.

## If you say no
Pages stay as files and no sign-up form goes live. The test then has no tranche 2 signal.

## What I am doing meanwhile
Nothing collected.
