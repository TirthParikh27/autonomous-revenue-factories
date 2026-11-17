# Spec: LedgerLite (working name) — 2026-11-17-private-spend-tracking-without-bank-login

**Job:** Lets a person who does not want to give an app their bank login see where their money went by importing the statement file their bank already gives them and categorising it on the device.

**Differentiation statement:** Unlike Monarch, Copilot, Rocket Money, Spendee and MonoBoost, this app builds the spending picture from a bank statement file (CSV or OFX) imported and parsed on the phone, with no bank login, no account and nothing uploaded, which matters because reviewers of these apps report bank-login demands, data selling, deletion that fails and unwanted AI (9 dated 2026 complaints, e.g. MonoBoost 2026-09-24 "This went directly for my bank log in and password", Rocket Money 2026-11-13 "The delete account button just spins", Copilot 2026-10-28 "AI does not need to know about our money"). Source: state/scout/2026-11-17-finance.json, fin-c4. Spot-checked 3 quotes against state/scout/reviews/ (found). The data-selling claims are reviewer claims, not verified; the spec and all copy make no claim about competitors' practices.

**Competitor table** (URLs from the scout file)
| App | URL | Lacks (per reviews) |
|---|---|---|
| Monarch | https://apps.apple.com/us/app/monarch-budget-track-money/id1459319842 | reviewers allege data sale, account deletion fails |
| Copilot | https://apps.apple.com/us/app/copilot-track-budget-money/id1447330651 | AI can't be turned off, worry about account access |
| Rocket Money | https://apps.apple.com/us/app/rocket-money-bills-budgets/id1130616675 | delete account spins |
| MonoBoost | https://apps.apple.com/us/app/monoboost-cancel-subscriptions/id6740202306 | asks for bank login directly, no manual bank add |
| Spendee | https://apps.apple.com/us/app/expense-budget-app-spendee/id635861140 | listed in scout file; one reviewer wants direct bank linking (points the other way) |
| Bills Manager | https://apps.apple.com/us/app/bills-manager/id834370671 | one data-scraping complaint |
Demand is mixed: the scout found no review asking for statement import in those words, and one Spendee reviewer wants bank linking. This is the weakest part of the spec. Manual spend trackers are also not sourced; the scout did not check how many exist.

**Core features** (at most 3)
1. On-device statement import: CSV or OFX file chosen from Files; parsed locally; duplicates detected across overlapping imports.
2. Local categorisation with rules the user can edit and a monthly spend view by category.
3. Real deletion and export: one tap erases all data on the device; export to CSV. No account exists to delete.

**Not building:** bank linking, aggregator integrations, advice or recommendations, AI categorisation (contradicts the pitch), net worth, investment tracking, cloud sync.

**Running cost:** none per subscriber (no server, no hosted model).

**Monetisation:** hard paywall after onboarding has imported a sample statement and shown the monthly picture. 7-day trial. Proposed price $4.99/month, an intention only; competitor prices unverified, demand-test must read them from the store pages first. Nothing charged at concept stage.

**Target market:** United States first (bank CSV formats vary by country). Median payer value is higher in North America than elsewhere (per CLAUDE.md; not in the scout file).

**Demand test plan**
- Page promise: "Track your spending without giving anyone your bank password." Concept page, "in development / early access", nothing charged.
- 6 post angles: (1) why does a budget app need my bank password; (2) download your bank's statement, see your month in 30 seconds; (3) delete everything in one tap; (4) no account, nothing to leak; (5) no AI reading your spending; (6) how to export a statement from the big US banks.

**Review risk:** 4.3(b) and 2.3 accuracy if copy implies things about competitors; 5.1.1 data and privacy label; financial-data handling expectations (no advice, no money movement, so not a lending or finance-regulated feature); 2.1 if CSV parsing breaks for common banks.

**Claims** (each needs evidence from the shipped build)
- "No bank login needed." — build has no aggregator or credential field.
- "Your statements stay on your phone." — network inspection.
- "Erase all your data in one tap." — test on a populated install.
Not claimed: anything about how other apps handle data.
