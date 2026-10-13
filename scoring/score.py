"""Fit + signal scoring with time decay, tiering and routing.

Usage: python3 scoring/score.py [--as-of YYYY-MM-DD]
Standard library only, so it runs anywhere.
"""
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Mirrors signals/signals.yml (kept inline to avoid a YAML dependency).
SIGNALS = {
    "reporting_product_hire":        {"weight": 30, "half_life": 45},
    "reporting_as_service_cost":     {"weight": 20, "half_life": 45},
    "large_customer_data_footprint": {"weight": 15, "half_life": 365},
    "pe_acquisition_recent":         {"weight": 30, "half_life": 120},
    "buy_and_build":                 {"weight": 15, "half_life": 365},
    "new_finance_leader":            {"weight": 25, "half_life": 90},
}

TIERS = [(45, "A"), (25, "B"), (0, "C")]
NEXT_ACTION = {
    "A": "research buying committee, one-to-one message on the strongest signal",
    "B": "templated message on the signal, persona from playbook",
    "C": "watch: wait for a second signal",
}


def fit_score(acc):
    """0 to 40. Size of the data problem, per hypothesis."""
    if acc["hypothesis"] == "H1":
        n = int(acc["end_customers"] or 0)
        return 40 if n >= 50000 else 30 if n >= 10000 else 20
    if acc["hypothesis"] == "H2":
        score = 20
        if acc["deal_type"] in ("carve_out", "first_outside_capital"):
            score += 10  # finance and data stack built from scratch
        if int(acc["acquisitions"] or 0) >= 10:
            score += 10
        return score
    return 0


def decayed(weight, half_life, age_days):
    return weight * 0.5 ** (max(age_days, 0) / half_life)


def main():
    as_of = date.today()
    if "--as-of" in sys.argv:
        as_of = date.fromisoformat(sys.argv[sys.argv.index("--as-of") + 1])

    accounts = list(csv.DictReader(open(ROOT / "data/accounts.csv")))
    signals = list(csv.DictReader(open(ROOT / "data/signals.csv")))

    rows = []
    for acc in accounts:
        own = [s for s in signals if s["account_id"] == acc["account_id"] and s["evidence_url"]]
        parts = []
        for s in own:
            cfg = SIGNALS[s["signal_type"]]
            age = (as_of - date.fromisoformat(s["observed_on"])).days
            parts.append((decayed(cfg["weight"], cfg["half_life"], age), s["signal_type"]))
        sig = sum(p for p, _ in parts)
        if len(parts) >= 2:
            sig *= 1.2  # stacking bonus: two independent signals
        fit = fit_score(acc)
        total = round(fit * 0.5 + sig, 1)
        tier = next(t for cut, t in TIERS if total >= cut)
        if tier == "A" and len(parts) < 2:
            tier = "B"  # one signal is a hint: tier A needs two stacked signals
        reason = max(parts)[1] if parts else "-"
        rows.append((total, acc["name"], acc["hypothesis"], fit, round(sig, 1), tier, reason))

    rows.sort(reverse=True)
    print(f"Scored as of {as_of}\n")
    print(f"{'Account':28} {'Hyp':3} {'Fit':>4} {'Sig':>5} {'Total':>6} Tier  Reason / next action")
    for total, name, hyp, fit, sig, tier, reason in rows:
        print(f"{name:28} {hyp:3} {fit:>4} {sig:>5} {total:>6}  {tier}    {reason}: {NEXT_ACTION[tier]}")


if __name__ == "__main__":
    main()
