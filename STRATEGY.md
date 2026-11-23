# STRATEGY.md — BTC 24h Race Bot: "Bounce Scalper"

## The strategy in one paragraph

A **trend-following scalper, long-only**. The bot trades only the confirmed
short-term up-moves (the bounces) inside the current downtrend and exits
fast. Entry: a Donchian breakout — the 1-minute close breaks above the
highest high of the last 120 bars (2 hours). Exit: whichever fires first of
four mandatory risk controls (fixed take profit, fixed stop loss, trailing
profit, trailing stop loss) or the Donchian channel exit (close below the
lowest low of the last 60 bars). Position size is 50% of cash per trade.
The bot never buys a flat or falling market, never shorts (shorts are
disabled by the competition), and never holds through a down-move.

## 1. Research: the current BTC trend (23 Nov 2026)

**Verdict: clear DOWNTREND — a bear market, Stage 4 (Declining).**

Evidence (checked 23 Nov 2026, sources: CoinDesk, Finnhub, TradingView):

- BTC ~$61,493 (23 Nov 2026). Peaked above **$126,000 in October 2025**
  (record $126,210 on 6 Oct 2025). Fell below **$57,000 on 20 Nov 2026**,
  its lowest since September 2024; fell to ~$55,900 on 21 Nov.
- Down **~55% from the October 2025 peak**; down 28% for the quarter;
  down ~25% in 1 month; down ~31% year-to-date; down ~30% in 1 year.
- November 2026 so far: **-22%** (the month is deeply red).
- The market keeps making **lower lows**. The next support is $54,000,
  then $53,000–$50,000. A move above $64,000 would be the first sign the
  trend is turning; until then, "the trend stays down" (CoinDesk/TradingView
  analyst consensus, 21 Nov 2026).
- Drivers: rising real US Treasury yields, a more hawkish Fed outlook,
  risk-off selling across stocks/gold/crypto, spot BTC ETF outflows
  (~$1.13B over 17–19 Nov), and $2.4B of liquidations in 24h on 20 Nov.
- Counted from the record high, the bear market is ~409 days old (21 Nov
  2026) — potentially the longest in Bitcoin's history (the 2013–2015 bear
  lasted ~410 days).

**Implication for the bot:** a long-only bot must NOT buy and hold in this
market — buy-and-hold would ride the downtrend down. It must scalp only
the confirmed short-term up-moves (bounces) and exit fast. The dev window
itself (22–23 Nov) was a **+3.64% bounce day** inside the downtrend
($58,957 → $61,102) — exactly the kind of day this bot harvests.

## 2. Research: the BTC 4-year (halving) cycle

**Verdict: we are in the post-peak BEAR phase of the 2024 halving cycle.**

- Halvings: 28 Nov 2012, 9 Jul 2016, 11 May 2020, **20 Apr 2024**
  (reward 6.25 → 3.125 BTC). Next halving ~April 2028.
- The pattern since 2016: the cycle peak arrives **17–18 months after the
  halving**, then a bear market of roughly a year, with a **77–85%
  drawdown** from peak to bottom.
- This cycle followed the script on timing: peak **$126,210 on 6 Oct 2025,
  ~534 days after the Apr 2024 halving** — right in the 17–18 month
  window (2017: ~525 days; 2021: ~547 days).
- The fall is **shallower than previous cycles so far**: -53% to ~$58,000
  by June 2026 (previous cycles fell 77–85%). The bottom typically comes
  ~12 months after the peak (~Oct–Nov 2026), so in Nov 2026 we are at or
  near the usual bottoming window — but the shallow drawdown means either
  the bottom is not yet in (more downside possible) or this cycle is
  structurally shallower (spot ETF demand).
- 2026 is the "second year after halving". Bitcoin has **never ended such
  a year green** (median -64.3% across the three prior cycles).

**Implication for the bot:** we are in the bear phase, not the bull phase.
The bot must be defensive: trade only confirmed up-moves, use a trailing
stop that locks in profit, never hold through a down-move, and keep a
drawdown guardrail (stop trading after -5% from peak equity). Volatility
is high (the dev window's 1-minute returns have an 8 bps standard
deviation, with single-minute moves up to ±0.7%), so stops must be sized
to the holding-period volatility, not to 1-minute noise (see §5).

## 3. Research: BTC's yearly / monthly history

- **Yearly returns:** 2024 **+121%**, 2025 **-5%**, 2026 YTD **-31%**.
  Down years: 2014 (-58%), 2018 (-69%), 2022 (-65%), 2025 (-5%). If 2026
  ends red, it will be the first time Bitcoin loses money two years in a
  row.
- **November is historically Bitcoin's BEST month:** median **+8.8%**,
  average +41.8%, green in 8 of 13 years (62%). Best month ever: Nov 2013
  (+454%). But November 2026 is **-22% so far** — the seasonal pattern is
  broken this year because the cycle (bear year) dominates the calendar.
- **December is typically weak:** median -3.2%, green in only 5 of 13
  years (38%).
- Q4 2026 so far: -28%.

**Implication for the bot:** do NOT rely on "November is usually strong"
seasonality — 2026 is breaking it. Follow the live trend (the Donchian
breakout), not the calendar. The bot has no seasonal bias in its code.

## 4. Whose approach this adapts (top world traders)

| Trader / system | What we took |
|---|---|
| **Turtle Traders** (Richard Dennis / William Eckhardt) — Donchian-channel breakout | The entry: buy a breakout to a new N-bar high, exit on a breakdown below an M-bar low. The original system used 20-day / 10-day channels; we use 120-minute / 60-minute channels for a 24h race. |
| **Mark Minervini** — Trend Template | "Buy only in a strong uptrend." Our breakout requires a new 2-hour high, which is the 1-minute equivalent of Minervini's price-above-rising-moving-averages filter. Strict stops, asymmetric payoff (risk a little to make more). |
| **Kristjan Qullamaggie** — momentum breakouts | Enter on a breakout with momentum confirmation (a new high, not a dip). Never buy a falling market. |
| **Ratchet / trailing-stop system** (TradingView "Trend Breakout & Ratchet Stop") | The staged exit: initial stop → breakeven lock once in profit → trailing stop below the highest high. Winners run while the trend lasts; losers are cut fast. |
| **Stan Weinstein** — stage analysis | Trade only in Stage 2 (Advancing). In Stage 4 (Declining) — where BTC is now — stay flat and scalp only the bounces. |
| **Jeremy Tan / TrendLogic** | Identify the dominant trend, enter on a breakout in its direction after confirmation, trail stops, cut losers quickly, exit on a trend break. |

We did **not** invent a strategy from scratch and we did **not** copy any
single system: the entry is Turtle/Minervini, the exits are the Ratchet
system, and the sizing is our own calibration to this competition's costs
(see §5).

## 5. The four mandatory risk controls (on EVERY trade)

Every trade the bot opens carries all four controls. They are checked on
every batch while a position is open, in this order: take profit, stop
loss, trailing profit / trailing stop, channel exit, time exit.

### Calibration: why these numbers

The competition's round-trip cost is ~26 bps at full size (4 bps fee +
2 bps slippage + ~7 bps constant-product impact each way against the
~$1.38M pool depth). The 1-minute return noise is ~8 bps (std dev), but
a trade held 30–120 minutes faces 50–90 bps of cumulative noise. So the
controls are sized to the **holding-period volatility**, not to 1-minute
noise. A tight stop (e.g. -30 bps) was backtested and LOSES money: it
fires 6 times on noise alone (net -$5.53). The numbers below are the
calibrated result.

| # | Control | Level | Reasoning |
|---|---|---|---|
| 1 | **TAKE PROFIT** (fixed) | **+300 bps (+3.0%)** above entry | A stretch target sized to the real moves: the dev window's big move was +3.2% in 2 hours. A hard cap that locks in a huge move. Rarely hit (0 times in the dev backtest) — it is the ceiling, not the usual exit. |
| 2 | **STOP LOSS** (fixed) | **-150 bps (-1.5%)** below entry | A crash-protection cap. ~2.4x the 1-hour noise (~62 bps), so it only fires on a genuine reversal, not on ordinary noise. Rarely hit (0 times in the dev backtest). No trade is ever opened without it. |
| 3 | **TRAILING PROFIT** | Activates at **+20 bps**; trails **20 bps** below the highest close since entry | The workhorse exit. Once the trade is +0.20% in profit, the exit level follows the highest price up: as the price makes new highs the level rises, so a winner keeps running while the trend continues and only exits on a 20 bps pullback, locking in the profit gained. In the dev backtest 5 of 7 round trips exited here. |
| 4 | **STOP TRAILING PROFIT** (trailing stop loss) | The stop ratchets: fixed SL (-150 bps) → **breakeven** at +20 bps → trails **20 bps** below the highest close | The stop itself moves up behind the price and never moves down. Before activation the stop is the fixed SL; once the trade is in profit the stop locks in breakeven, then trails. If the price reverses to the trailing stop, the trade closes and the profit already made is kept. |

Additional exits: the Donchian channel exit (close below the 60-bar low —
the uptrend is over), a time exit (close a scalp older than 6 hours), and
a drawdown guardrail (stop trading for the rest of the window if equity
falls 5% below its peak; the competition disqualifies entries over 25%
max drawdown).

### Position sizing

**50% of cash per trade.** Halving the size (vs all-in) roughly halves
the constant-product price impact (~7 bps → ~3.5 bps each way at the
frozen depth), which is worth more than the extra size on a scalp. The
bot holds at most 1 position (the competition's cap).

## 6. Backtest results (frozen dev window, 1440 x 1m bars)

Local backtest replaying the dev window through the bot (`backtest.py`,
same fill model as the harness: fee 4 bps, slippage 2 bps,
constant-product impact against each bar's open depth):

| Metric | This bot | Buy-and-hold (same window) |
|---|---|---|
| Net PnL | **+$6.36** | +$36.39 |
| Trades | 14 legs (7 round trips) | 1 |
| Max drawdown | **0.77%** | ~3.9% (intra-day) |
| Exits | 5 trailing-stop, 2 channel, 0 TP, 0 SL | — |

The bot passes the dev gate (net PnL > $0). Buy-and-hold scores higher
on this one up day, but it would lose on a down day; this bot only risks
capital on confirmed up-moves, so it is built for the race window
(unknown direction) rather than for this one dev day.

Robustness (nearby parameters, same backtest): the strategy stays
profitable for Donchian (100–130, 50–70), trail 15–20 bps, size 0.4–0.6
(+$0.91 to +$8.45). It is not a single overfit point.

## 7. What the bot does NOT do

- No mean-reversion, no range trading against the trend, no buying dips
  in a downtrend.
- No shorts, no leverage (both disabled by the competition anyway).
- No martingale / averaging down: one position at a time, one entry per
  breakout, no adding to a losing trade.
- No network, no wall clock, no files outside the repo, no unseeded
  randomness. Deterministic: two runs on the same data produce identical
  orders.
- Never crashes on bad input: missing bars, rejected fills, and any
  unexpected error are handled by answering with no orders and continuing.
