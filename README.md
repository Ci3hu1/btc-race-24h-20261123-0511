# BTC 24h Race Bot — "Bounce Scalper"

[![make.fun bounty](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/Ci3hu1/btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/Ci3hu1/btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)

A trend-following scalping bot for
[make.fun's "Race a BTC trading bot live for 24 hours" bounty](https://make.fun/bounty/btc-race-24h-20261123-0511)
(referral: `cc7tcnw6`). It races a simulated $1,000 of cbBTC (Coinbase
Wrapped BTC) on Solana for 24 hours, long-only, pure Python standard
library.

## Strategy

**Scalping with the trend, never against it.** BTC is in a bear market in
November 2026 (peaked ~$126,210 in Oct 2025, ~55% down to ~$55,900 by
21 Nov), so a long-only bot must not buy and hold — it scalps only the
confirmed short-term up-moves (the bounces) inside the downtrend and
exits fast. See [STRATEGY.md](STRATEGY.md) for the full research: the
current trend, the 4-year halving cycle, BTC's yearly/monthly history,
and the top traders whose approach this adapts (Turtle Traders'
Donchian breakout, Minervini's Trend Template, Qullamaggie's momentum
breakouts, the Ratchet trailing-stop system, Weinstein's stage analysis).

- **Entry:** Donchian breakout — the 1-minute close breaks above the
  highest high of the last 120 bars (2 hours).
- **Exits (every trade carries all four):**
  1. **Take profit** — fixed +3.0% above entry.
  2. **Stop loss** — fixed -1.5% below entry.
  3. **Trailing profit** — activates at +0.20%; trails 0.20% below the
     highest close since entry, so a winner keeps running while the
     trend continues.
  4. **Stop trailing profit** — the stop ratchets to breakeven at +0.20%,
     then trails 0.20% below the highest close; a reversal closes the
     trade with the profit locked in.
  Plus a Donchian channel exit (close below the 60-bar low), a 6-hour
  time exit, and a -5% drawdown guardrail.
- **Size:** 50% of cash per trade (halves the price impact vs all-in).

## Backtest (frozen dev window, 1440 x 1m bars)

| Metric | This bot | Buy-and-hold |
|---|---|---|
| Net PnL | **+$6.36** | +$36.39 |
| Trades | 14 legs (7 round trips) | 1 |
| Max drawdown | **0.77%** | ~3.9% |

Passes the dev gate (net PnL > $0). Buy-and-hold scores higher on this
one up day, but it would lose on a down day; this bot only risks capital
on confirmed up-moves.

## Run

```sh
python3 -P -s main.py   # speaks agent-fun/bars-replay/v1 on stdin/stdout
```

Tests:

```sh
python3 tests/test_bot.py
```

## Files

- `main.py` — the bot (pure stdlib; vendors the kit SDK under `vendor/`).
- `STRATEGY.md` — the strategy, the research, and the risk-control calibration.
- `tests/test_bot.py` — 13 tests covering all four risk controls, the
  entry, staying flat in a downtrend, and robustness.
- `backtest.py`, `tune.py`, `variants*.py`, `robust.py`, `final_test.py` —
  the local backtest harness and parameter-tuning scripts used to build it.

## License

MIT. See [LICENSE](LICENSE).
