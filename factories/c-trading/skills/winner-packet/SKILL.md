---
name: winner-packet
description: The only stage of Factory C that contacts the operator about a strategy. Use when an item is at `confirmed` and has no packet yet, to assemble the evidence and raise `F-CAP-1`. Never use for a strategy that has not passed the exam and a full paper period.
---

# Winner packet

Read `CLAUDE.md`, `ESCALATION.md` and `budget.yaml` first. The operator asked to hear about a strategy only when it is proven as far as this factory can prove anything. This packet is that message, so it must be exact about what is known and what is not.

## Steps

1. Take each item at `confirmed` with no packet in `escalations/`. If its `health/<id>.json` is not `in_range` today, stop: it goes back to `maintain`.
2. Call the `reviewer` agent with the task `result` on the current files. If it rejects, move the item back to `paper` with the reason and write no packet.
3. Write the packet with the shared `escalate` skill, trigger `F-CAP-1`, with the nine parts listed in `ESCALATION.md`. Copy every figure from its file and give the path:
   - the card and its commit;
   - `state/gate/<id>.json`: trials on the dataset, distinct ideas, this strategy's own trials, the deflated Sharpe ratio, and the supporting evidence;
   - `exam/<id>.json`: the checks and the unseen window;
   - `paper/<id>.json` and `health/<id>.json`: start, days, paper result, benchmark, market-adjusted result, drawdown, and where the record sits in its predicted range;
   - `paper/book.json`: the combined book's record and the strategies in it;
   - `strategies/<id>/maintenance/`: every action taken;
   - the reviewer's remaining weaknesses, word for word.
4. State the confidence in plain words, using these facts and no stronger ones:
   - The deflated Sharpe ratio is the chance the backtest result is not luck, given every trial counted.
   - The exam removed about half of lucky results in testing (`FACTORY_SPEC.md` section 9).
   - The paper period shows the strategy behaved as its backtest predicted on prices that did not exist when it was built. It is too short to prove the edge on its own.
   - Fills and costs are the engine's model. No real order has been placed.
5. Move the item to `awaiting_human`.

## Never

- Never call a strategy profitable, proven or safe. Say what was measured.
- Never leave out a failed variant, a maintenance action or a weakness.
- Never recommend an amount of money or a broker. Live trading is not part of this factory.

## Finish

End with the shared `run-report` skill.
