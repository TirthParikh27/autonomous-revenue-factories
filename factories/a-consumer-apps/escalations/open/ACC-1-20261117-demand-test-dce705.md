# Create or confirm the accounts the demand test needs: Meta Ads, Cloudflare Pages, Supabase
Factory: a-consumer-apps   Item: batch 2026-11-17-b1   Trigger: ACC-1   Raised: 2026-11-17   Expires: 2026-11-24

## What I want to do
Nothing myself. I need you to confirm these accounts exist, or create them, so the batch can go live.

## Why now
- Meta Ads account: three paused campaigns, plus a pixel id for the page events. You set the account spending limit.
- Cloudflare Pages: deploys `demand/<id>/site/` from CI on merge. No agent holds the hosting token.
- Supabase: early-access table (email, consent timestamp, idea id) and a publishable key for the form. See `PII-1`.
Plans and prices: not looked up this run, so unverified. Free tiers are expected for Cloudflare Pages and Supabase (`FACTORY_SPEC.md` section 6).

## Cost and worst case
Ad spend is in `A-AD-1`. The vendors hold only the data listed in `PII-1` and ad-account details. Worst case: ad account restricted.

## How to undo it
Close each account in its vendor settings.

## If you say no
Batch stays as files.

## What I am doing meanwhile
Nothing needing an account.
