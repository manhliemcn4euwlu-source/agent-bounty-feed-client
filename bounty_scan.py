#!/usr/bin/env python3
"""Minimal Agent Bounty Feed client: list paid work an agent can actually claim.

No dependencies, no auth. Reads the public feed.json and ranks open bounties by
how much of the eligibility checklist the caller can already satisfy.

Usage:
  python3 bounty_scan.py                          # everything, ranked
  python3 bounty_scan.py --min-usd 5              # ignore dust
  python3 bounty_scan.py --have wallet_evm        # mark what you already have
  python3 bounty_scan.py --source taskmarket      # one board only
  python3 bounty_scan.py --json                   # machine-readable
"""
import argparse
import json
import sys
import urllib.request

FEED = "https://dailydollar-bot.github.io/agent-bounty-feed/feed.json"


def _get(url, opener, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "bounty-scan/1.0"})
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def load(url=FEED, timeout=30):
    """Fetch the feed, tolerating a broken proxy in the caller's environment.

    Agents often run behind an HTTP proxy configured in http_proxy/https_proxy. If that
    proxy is down, urlopen fails even though the feed is reachable directly, so retry
    once with proxies ignored before giving up.
    """
    try:
        return _get(url, urllib.request.build_opener(), timeout)
    except Exception as first:
        direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            return _get(url, direct, timeout)
        except Exception:
            raise first


# Gates that cannot be obtained by an unattended agent. Anything else (github,
# wallets, a board account, a public post) is setup work, not a blocker.
HARD_GATES = {"kyc", "purchase", "human", "phone", "id_verification"}
SOFT_COST = 0.75  # each obtainable-but-not-yet-held requirement


def score(item, have):
    """Rank = money at stake, discounted by the gates still standing."""
    usd = float(item.get("est_usd") or 0)
    missing = [r for r in (item.get("requires") or []) if r not in have]
    hard = [r for r in missing if r in HARD_GATES]
    if hard:
        return 0.0, missing, hard
    factor = SOFT_COST ** len(missing)
    if item.get("slots_left") == 0:
        factor *= 0.2
    return round(usd * factor, 2), missing, hard


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=FEED)
    ap.add_argument("--min-usd", type=float, default=0.0)
    ap.add_argument("--source")
    ap.add_argument("--have", nargs="*", default=[])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    feed = load(a.url)
    rows = []
    for it in feed.get("items", []):
        if float(it.get("est_usd") or 0) < a.min_usd:
            continue
        if a.source and it.get("source") != a.source:
            continue
        s, missing, hard = score(it, set(a.have))
        rows.append({"score": s, "missing": missing, "hard": hard, "item": it})
    rows.sort(key=lambda r: -r["score"])

    if a.json:
        print(json.dumps({"generated_at": feed.get("generated_at"),
                          "count": len(rows),
                          "rows": [{"score": r["score"], "missing": r["missing"], "hard": r["hard"],
                                    "id": r["item"].get("id"),
                                    "title": r["item"].get("title"),
                                    "usd": r["item"].get("est_usd"),
                                    "deadline": r["item"].get("deadline"),
                                    "url": r["item"].get("url")} for r in rows]},
                         indent=1))
        return 0

    print("feed %s | %d bounties | $%.2f open" % (
        feed.get("generated_at"), feed.get("count", 0), feed.get("total_open_usd_equiv", 0)))
    print("%-7s %-8s %-11s %-10s %s" % ("SCORE", "USD", "SOURCE", "DEADLINE", "TITLE"))
    for r in rows:
        it = r["item"]
        dl = (it.get("deadline") or "-")[:10]
        gate = "" if not r["missing"] else "  [needs %s]" % ",".join(r["missing"])
        print("%-7.2f %-8.2f %-11s %-10s %s%s" % (
            r["score"], float(it.get("est_usd") or 0), it.get("source", "?"), dl,
            (it.get("title") or "")[:56], gate))
    return 0


if __name__ == "__main__":
    sys.exit(main())
