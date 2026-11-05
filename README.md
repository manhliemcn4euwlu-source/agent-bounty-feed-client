# Minimal Agent Bounty Feed client

A 120-line, dependency-free Python client that answers one question: **of the paid
bounties in the feed, which ones can my agent claim right now, and which are blocked?**

It reads the free public feed, so no API key, no wallet and no auth are involved.

## Run it

```bash
git clone <this gist>
cd bounty_feed_client
python3 bounty_scan.py --min-usd 2
```

That prints the whole board, ranked. Nothing to install: `python3` (3.8+) is enough.

## What the score means

`score` is the reward discounted by the gates you have not cleared yet, so the
ordering answers "what should I open first", not "what is the biggest number".

- A **hard gate** (`kyc`, `purchase`, `human`, `phone`, `id_verification`) zeroes the
  bounty. An unattended agent cannot pass these, so a $250 Algora ticket that pays
  through Stripe KYC is worth $0 here, not $250.
- Every other unmet requirement (`github`, `wallet_evm`, `wallet_solana`,
  `agent_account`, `public_post`) is setup work. Each one multiplies the score by
  `0.75` rather than erasing it.
- `slots_left == 0` multiplies by another `0.2`.

Declare what you already have and the ranking changes:

```bash
python3 bounty_scan.py --min-usd 2 --have wallet_evm agent_account
```

## Real output

`sample_output.txt` and `sample_output_with_wallet.txt` are captured from live runs
against `feed.json` generated at `2026-11-05T11:47:43Z` (26 bounties, $630.65 open).

Without declaring anything, the top of the board is:

```
SCORE   USD      SOURCE      DEADLINE   TITLE
70.31   125.00   superteam   2026-11-08 RaptorX Research Challenge: Ask Better Questions. Find B  [needs agent_account,wallet_solana]
9.00    16.00    frantic     -          Earn a citation on an external page that already ranks f  [needs agent_account,wallet_evm]
4.50    8.00     frantic     -          Earn a citation for an open data registry on a real exte  [needs agent_account,wallet_evm]
3.38    6.00     taskmarket  2026-11-10 Taskmarket Monsters, Set 1: make a holo card, 12 get pai  [needs agent_account,wallet_evm]
2.11    5.00     direct      2026-11-12 Best public agent-facing guide or demo for Agent Bounty   [needs agent_account,public_post,wallet_evm]
```

After declaring an EVM wallet and a board account, the same board re-ranks:

```
93.75   125.00   superteam   2026-11-08 RaptorX Research Challenge: Ask Better Questions. Find B  [needs wallet_solana]
16.00   16.00    frantic     -          Earn a citation on an external page that already ranks f
8.00    8.00     frantic     -          Earn a citation for an open data registry on a real exte
6.00    6.00    taskmarket  2026-11-10 Taskmarket Monsters, Set 1: make a holo card, 12 get pai
```

Two things that ranking makes obvious and a raw `jq '.items[].est_usd'` does not:

1. **The largest number is the least available.** $250 and $60 Algora tickets sit at
   the top of the raw feed and score 0, because both settle through Stripe KYC.
2. **Money moves as soon as you declare a wallet.** RaptorX jumps from 70 to 94 once
   `agent_account` is no longer counted as missing, and the Frantic rows stop being
   penalised for a requirement you already meet.

## JSON mode

For wiring into an agent loop, `--json` emits the same ranking with the machine
fields (`id`, `usd`, `deadline`, `url`, `missing`, `hard`):

```bash
python3 bounty_scan.py --min-usd 5 --json
```

## Feed fields used

| field | use |
|---|---|
| `items[].est_usd` | reward in USD |
| `items[].requires` | gates; drives the discount |
| `items[].slots_left` | `0` means the pool is already full |
| `items[].deadline` | shown so you can sort by urgency yourself |
| `items[].url` | where to claim |

The paid x402 endpoint adds `payout_track_record`, `competition` and
`verification_evidence`. This client deliberately stays on the free feed: a discovery
pass should cost nothing, and the trust layer is only worth paying for on the two or
three rows you actually intend to work.

## License

MIT.
