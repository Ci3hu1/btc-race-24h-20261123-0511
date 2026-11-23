# NOTES.md — btc-race-24h-20261123-0511

## Entry

- Repo: https://github.com/Ci3hu1/btc-race-24h-20261123-0511
- Competition: btc-race-24h-20261123-0511 — "Race a BTC trading bot live
  for 24 hours". $50 total (10 paid places, $12 top). FREE, no
  prerequisites. Entries close 23 Nov 2026 18:11 WIB (2026-11-23T11:11:00Z).
- Title: "BTC 24h race: Bounce Scalper — trend-following scalper, long-only".
- Status: built, bundled, kit-checked. **NOT submitted** — awaiting Joni's
  explicit "Setuju" on the exact entry.

## Strategy (summary; full version in STRATEGY.md)

Trend-following scalper, long-only, adapted from top traders (Turtle
Donchian breakout, Minervini Trend Template, Qullamaggie momentum
breakouts, Ratchet trailing-stop system, Weinstein stage analysis).
Entry: Donchian breakout above the 120-bar (2h) high. Four mandatory
risk controls on EVERY trade: take profit +3.0%, stop loss -1.5%,
trailing profit (activates +0.20%, trails 0.20% below the highest close),
stop trailing profit (stop ratchets to breakeven at +0.20%, then trails
0.20% below the highest close). Plus a Donchian channel exit (60-bar
low), a 6-hour time exit, a -5% drawdown guardrail. Position size 50%
of cash.

Research (23 Nov 2026): BTC is in a BEAR market (peaked $126,210 on
6 Oct 2025, ~534 days after the Apr 2024 halving; -55% to ~$55,900 on
21 Nov 2026). 4-year cycle: post-peak bear phase, bottom typically
~12 months after the peak. November is historically BTC's best month
(median +8.8%) but 2026 is the "second year after halving" (never ended
green, median -64.3%) and Nov 2026 is -22% so far — cycle dominates
seasonality, so the bot follows the live trend, not the calendar.

## Requirements followed

- Protocol agent-fun/bars-replay/v1 (NDJSON on stdin/stdout; hello, then
  one batch per minute, then done; exactly one reply per batch).
- Pure Python stdlib only for the graded program (main.py + vendored kit
  SDK under vendor/). No numpy/pandas/third-party.
- main.py is written in-session (NOT byte-for-byte the kit starter).
- Deterministic: no network, no wall clock, no files outside the repo,
  no unseeded randomness.
- Robust: missing bars, rejected fills, and unexpected errors are handled
  by answering with no orders and continuing (a crash mid-race scores 0).
- Tests + STRATEGY.md (non-blank) at root. README with 3 live make.fun
  badges naming the actual repo + bounty link + referral cc7tcnw6.
- About: homepage https://make.fun/bounty/btc-race-24h-20261123-0511,
  topics makefun, ai-agents, bounties. LICENSE MIT with SPDX line.

## Test results

- Unit tests: **13/13 pass** (`python3 tests/test_bot.py`) — covers all
  four risk controls (TP closes at +3.0%, SL closes at -1.5%, trailing
  stop locks in profit on a reversal, trailing profit rises with price),
  the breakout entry, staying flat in a downtrend, the channel exit,
  missing bars, determinism, and the drawdown guardrail.
- Local backtest on the frozen dev window (1440 x 1m bars,
  `backtest.py`): **net PnL +$6.36, 14 legs (7 round trips), max drawdown
  0.77%** — passes the dev gate (net PnL > $0). Buy-and-hold on the same
  window: +$36.39 (but it would lose on a down day).
- Parameter tuning: the first scalping design (EMA 8/21 + breakout,
  tight TP/SL) LOST money on every one of 1,536 parameter combinations
  (best -$38.94) — EMA crossovers whipsaw on 1-minute noise. The
  Donchian breakout + trailing stop was the first design to profit, and
  a tight fixed TP/SL (-30/+80 bps) destroyed it (-$5.53, 6 SL exits on
  noise); the calibrated wide caps (+300/-150 bps, sized to the
  holding-period volatility) preserve the edge (+$6.36). Robustness:
  nearby parameters (Donchian 100–130 / 50–70, trail 15–20 bps, size
  0.4–0.6) all stay profitable (+$0.91 to +$8.45).
- Grader-conditions check: main.py run as uid 65534 on a read-only repo
  copy produces byte-identical output (see below).

## Kit check

- Kit: fresh download 23 Nov 2026 to
  ~/workspace/tools/makefun/btc-race-24h-20261123-0511-kit/ (CLI at
  .../cli/makefun.mjs).
- Bundle: ~/workspace/tools/makefun/bundles/btc-race-20261123-0511-bundle.tar.gz
- Check: `node cli/makefun.mjs check --json --repo <local> --commit <sha>
  --transcripts <tarball>` → ok=true, failed=[] (see the bundle/check
  report from the parent agent).

## Files in this repo

- main.py — the bot.
- vendor/makefun_bars.py — the kit's Python SDK (byte-for-byte copy,
  excluded from authorship counts).
- STRATEGY.md, README.md, LICENSE, NOTES.md, tests/test_bot.py.
- backtest.py, tune.py, variants.py, variants2.py, variants3.py,
  robust.py, final_test.py — the local backtest + tuning scripts used
  to build the bot; they live outside the repo in
  ~/workspace/tools/makefun/btc-race-dev/ (dev aids, not part of the
  graded program).

## Submission
- Submission: 01a2074a-d138-76c0-bbfb-b29676101896 (submitted 23 Nov 2026 ~14:24 WIB on Joni's "Setuju")
- Entry commit: b9057a29192d485229685abc06137b7403a34a78
- Stage: scored (passed checks)
- Bundle: ~/workspace/tools/makefun/bundles/btc-race-20261123-0511-bundle.tar.gz (466,230 B, sha256 d11d0a0754b616900a2b2e636749eb05b72a61902c24f36057800485bf9a3779)
- Kit check: ok=true, failed=[] (3 intake items deferred to server, all hand-verified: repo created 07:08:16Z after open 05:11:00Z, commit in repo, original files)
- Claim code: saved ONLY in ~/.config/makefun/btc-race-24h-20261123-0511-submission.json (0600)
