# GTM data architecture: a worked example

A small, self-contained example of how I structure the data side of go-to-market: which entities exist, how buying signals are defined and stacked, how accounts get scored and routed, and who gets contacted with what.

The example uses only public data (job posts, PE deal announcements) collected on 7 October 2026 for two targeting hypotheses. No client data is included.

## Layout

| Path | What it is |
| --- | --- |
| `sql/schema.sql` | Data model: accounts, contacts, signals, scores, touches, deals. Warehouse-agnostic SQL. |
| `signals/signals.yml` | Signal catalogue: definition, source, weight, decay, evidence rule. |
| `data/accounts.csv`, `data/signals.csv` | Sample accounts and the observed signals behind them. |
| `scoring/score.py` | Fit plus signal scoring with time decay, tiering and routing. Standard library only. |
| `playbook/personas.md` | Who we contact per hypothesis, why, and the opening angle. |
| `playbook/qualification.md` | Qualification questions mapped to budget, fit, timing, decision. |
| `playbook/operating-rhythm.md` | How the work runs week to week at 20 hours. |

## Run it

```
python3 scoring/score.py
```

Prints every account with fit score, signal score, total, tier and the next action.

## Principles

1. Won deals first. Hypotheses here are starting points; the first real step is checking them against the last 10 to 15 won deals and keeping only what matches how the company actually wins.
2. Every signal carries evidence (URL, date, quote). No evidence, no score.
3. Signals decay. A job post from August is worth less than one from last week.
4. One signal is a hint, two stacked signals are a reason to reach out.
5. Scores route work, people make the call. Tier A gets a researched one-to-one message, tier B a templated one, tier C waits for another signal.

## Sample output

Run on 13 October 2026: Storable, Owner.com, ezCater and Ranger Fire and Security land in tier A (two stacked signals each). Accounts with one signal stay in B or C until a second one appears.

Evidence URLs in `data/signals.csv` point to the source site of each signal; in a live setup each row stores the exact post or announcement link.
