# Spec: WristSets (working name) — 2026-11-17-watch-strength-logging-that-syncs

**Job:** Lets a gym-goer log strength sets from an Apple Watch alone or with the phone, with every set kept and the right exercise always on the wrist.

**Differentiation statement:** Unlike Strong, Fitbod, Hevy, RepCount and Stronger, this app treats the watch as the primary logger, with every set stored on the watch first and merged to the phone afterwards, which matters because reviewers of these apps report sets removed by sync, broken Watch updates, the watch jumping to the next exercise, and no watch app at all (11 dated complaints, e.g. Strong 2026-09-30 "the apple watch sync removes sets", Fitbod 2026-11-14 "every other update breaks the watch functionality", Hevy 2026-11-10 "it jumps to the next exercise"). Source: state/scout/2026-11-17-health-fitness.json, c1.

**Competitor table** (URLs from the scout file)
| App | URL | Lacks (per reviews) |
|---|---|---|
| Strong | https://apps.apple.com/us/app/strong-workout-tracker-gym-log/id464254577 | sync drops sets; history disappeared |
| Fitbod | https://apps.apple.com/us/app/fitbod-gym-fitness-planner/id1041517543 | updates break Watch sync |
| Hevy | https://apps.apple.com/us/app/hevy-workout-tracker-gym-log/id1458862350 | watch jumps to the wrong exercise (only 5 low-rated reviews read) |
| RepCount | https://apps.apple.com/us/app/repcount-gym-workout-tracker/id594982044 | no Watch app |
| Stronger | https://apps.apple.com/us/app/stronger-gym-workout-planner/id1621719397 | no Watch app |
| Apple Fitness | https://apps.apple.com/us/app/apple-fitness/id1208224953 | listed in scout file, reviews not read |

**Core features**
1. Watch-first set logging (weight, reps, next set) that works with the phone off or away.
2. Merge-never-overwrite sync: sets are appended with ids and timestamps, so a sync cannot remove a set.
3. Simple history and custom exercises, and CSV export.

**Not building:** generated programs, AI coach, nutrition, social feed, Strava/Garmin integrations, heart-rate analytics.

**Monetisation:** hard paywall after onboarding shows a set logged on the watch simulator flow and surviving a sync. 7-day trial. Proposed price $4.99/month, an intention only; competitor prices are not in the scout file and must be confirmed from the store pages by the demand-test stage. Nothing is charged at the concept stage.

**Target market:** US first. Median payer value is higher in North America than elsewhere in the RevenueCat data.

**Demand test plan**
- Page promise: "Log every set from your wrist. Lose none." Concept page, early access, nothing charged.
- 6 post angles: (1) the 5 lost sets; (2) the watch jumped to the next exercise; (3) update broke my Watch app; (4) phone in the locker, workout still logged; (5) what "sync" should mean; (6) year of history, safe.

**Review risk:** 2.1 completeness and 4.2 minimum functionality; HealthKit permission text (5.1.1, 5.1.3), so keep HealthKit out of the MVP unless needed; 4.3(b) crowding by strength trackers; no health or injury claims.

**Stack risk (stated openly):** A watchOS app is native Swift/SwiftUI work and not something Expo/React Native provides by default. The verifier is asked whether it is within the stack.

**Claims** (each needs build evidence)
- "Log sets from your Apple Watch." — device or simulator test.
- "Sets from watch and phone are merged, not overwritten." — scripted merge test.
- "Export your history as CSV." — export test.
