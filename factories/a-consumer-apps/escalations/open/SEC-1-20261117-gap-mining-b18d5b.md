# SEC-1: instruction-like text in fetched reviews
Raised by run 20261117T072756Z-gap-mining-b18d5b, 2026-11-17.

## Source and text (quoted as data)
1. Business scout, Invoice Simple review dated 2025-11-18 (Apple review RSS feed for Invoice Simple, listed in state/scout/2026-11-17-business-b.json): text ends with chatbot-pasted wording telling the reader to tweak the review and post it on the App Store and Google Play.
2. Health and Fitness scout, Fitbod reviews (state/scout/2026-11-17-health-fitness.json, injection_suspected, lines 7-20): "Alternative: turn to LLM, tell it the gym equipment you're using..." and "Fitbod has gotten so bad go to gravl". Low confidence: reviewer opinion or competitor promotion, not aimed at an agent.

## What the run had access to
Read, Write, Agent (market-scout, no credentials, no write connectors). No credentials, no ledger spend. Nothing was followed or passed on as instructions.

## Handling
- Business file marked quarantined (marker in state/scout/quarantine/; the file itself could not be moved because mkdir and mv were denied). No Business items created.
- Health items created (c1, c5) use no Fitbod evidence; the flagged reviews relate to c4/c7, which were dropped.

## Decision needed
Confirm quarantine of the Business file, and say whether it may be re-read for a later run.
