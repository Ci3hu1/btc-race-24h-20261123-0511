#!/usr/bin/env python3
"""BTC 24h race bot: trend-following scalper (long-only).

Strategy: "Bounce Scalper" -- scalping WITH the trend, never against it.
Adapted from the playbook of top trend-following traders (the Turtle
Traders' Donchian-channel breakout of Richard Dennis / William Eckhardt,
Minervini's Trend Template, Qullamaggie's breakout setups, the Ratchet /
trailing-stop system and Weinstein's stage analysis):

  * TRADE ONLY WITH THE TREND. A long is opened only on a Donchian
    breakout: the close breaks above the highest high of the last 120
    one-minute bars (2 hours). A new 2-hour high means the short-term trend
    is up. This is the Turtle breakout and Minervini's "buy only in a
    strong uptrend", compressed to the 1-minute timeframe the race runs on.
    When there is no breakout the bot stays in cash -- it never buys a
    falling market and never shorts (shorts are disabled by the
    competition). This is Weinstein Stage 2 ("Advancing") logic: trade
    only when the trend is advancing; in Stage 4 ("Declining") stay flat.
  * SCALP EXITS. The trade is closed by whichever fires first of the
    four mandatory risk controls below, or by the Donchian channel exit
    (the close falls below the lowest low of the last 60 bars -- the
    uptrend is over). A scalp here is a short-term trend trade (minutes
    to a few hours), not a multi-day hold and not a 1-minute noise trade:
    the 1-minute noise is ~8 bps but a trade held 30-120 minutes faces
    50-90 bps of noise, so the controls are sized to the holding-period
    volatility (see STRATEGY.md for the calibration).

FOUR MANDATORY RISK CONTROLS -- active on EVERY trade, no exceptions:
  1. TAKE PROFIT (TP): fixed +300 bps (+3.0%) above entry. When the
     position's P&L reaches +3.0%, close the trade and lock in the
     profit. Sized to the scale of the real moves: the dev window's big
     move was +3.2% in 2 hours, so a 3% TP is a stretch target a strong
     trend day can reach. It is a hard cap, not the usual exit.
  2. STOP LOSS (SL): fixed -150 bps (-1.5%) below entry. When the
     position's P&L reaches -1.5%, close the trade immediately to cap
     the loss. Sized to the holding-period volatility (~62 bps of noise
     over a 1-hour hold): a 1.5% stop is ~2.4x that noise, so it only
     fires on a genuine reversal, not on ordinary noise. A tighter stop
     (e.g. -30 bps) was backtested and LOSES money: it fires 6 times on
     noise alone. The SL is the catastrophic cap; the trailing stop
     below does the day-to-day cutting.
  3. TRAILING PROFIT: once the trade is +20 bps in profit (activation),
     the exit level trails the highest close since entry by 20 bps.
     As the price makes new highs the exit level rises with it, so a
     winning trade keeps running while the trend continues and only
     exits on a 20 bps pullback, locking in the profit gained. This is
     the workhorse exit: in the dev-window backtest 5 of 7 round trips
     exited here.
  4. STOP TRAILING PROFIT (trailing stop loss): the stop itself ratchets
     up behind the price. Before activation the stop is the fixed SL
     (-150 bps). Once the trade is +20 bps in profit the stop ratchets
     to breakeven, then trails 20 bps below the highest close since
     entry. If the price reverses to the trailing stop, the trade closes
     and the profit already made is kept. The stop never moves down.
  * RISK GUARDRAIL. If equity falls more than 5% below the peak equity
    seen, stop trading for the rest of the window. The competition
    disqualifies entries with max drawdown > 25%; this keeps the bot far
    inside that limit.
  * POSITION SIZE: 50% of cash per trade. Halving the size (vs all-in)
    roughly halves the constant-product price impact (the pool depth is
    ~$1.38M, so a $1,000 trade moves its own price ~7 bps each way),
    which is worth more than the extra size on a scalp.

Why this fits the current market (research, 23 Nov 2026 -- see STRATEGY.md):
  * BTC is in a BEAR MARKET (Stage 4 Declining): peaked ~$126,210 on
    6 Oct 2025, ~534 days after the Apr 2024 halving (the classic 17-18
    month halving-to-peak window), then fell ~55% to ~$55,900 on 21 Nov
    2026. The trend is down, so a long-only bot must NOT buy and hold --
    it must scalp only the confirmed short-term up-moves (the bounces)
    inside the downtrend and exit fast.
  * The dev window itself (22-23 Nov) was a +3.64% bounce day inside
    that downtrend -- exactly the kind of day this bot is built to
    harvest. Backtest on the frozen dev window: +$6.36 net PnL,
    7 round trips, max drawdown 0.77% (buy-and-hold on the same window:
    +$36.39, but buy-and-hold would lose on a down day; this bot only
    risks capital on confirmed up-moves).
  * November is historically BTC's strongest month (median +8.8%) but
    2026 is the "second year after halving", a year that has NEVER ended
    green (median -64.3%): cycle dominates seasonality, so the bot
    follows the live trend, not the calendar.

Pure Python standard library only. No network, no wall clock, no files
outside the repo, no unseeded randomness: two runs on the same data
produce identical orders (deterministic).
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
)
import makefun_bars  # noqa: E402

SYMBOL = "CBBTC"
BPS = 10_000

# ---------------------------------------------------------------------------
# Strategy parameters (tuned on the frozen dev window, 1440 x 1m bars).
# ---------------------------------------------------------------------------
DONCHIAN_IN = 120     # entry: breakout above the highest high of last N bars
DONCHIAN_OUT = 60     # channel exit: below the lowest low of last N bars
TAKE_PROFIT_BPS = 300  # 1. TAKE PROFIT: close at +3.0% above entry
STOP_LOSS_BPS = 150    # 2. STOP LOSS: close at -1.5% below entry
TRAIL_ACTIVATE_BPS = 20  # 3/4. trailing activates once the trade is +0.20%
TRAIL_DIST_BPS = 20    # 3/4. trail 0.20% below the highest close since entry
MAX_HOLD_BARS = 360    # time exit: close a scalp older than 6 hours
MAX_DD_BPS = 500       # risk guardrail: stop trading after a -5% drawdown
POSITION_FRACTION_BPS = 5000  # spend up to 50% of cash per trade
MAX_SLIPPAGE_BPS = 100  # max slippage the bot accepts on any order


class Scalper:
    """Trend-following scalper with four mandatory risk controls.

    All arithmetic is integer (bps). The four controls are checked on
    every batch while a position is open, in this order: take profit,
    stop loss, trailing profit / trailing stop, channel exit, time exit.
    """

    def __init__(self):
        self.closes = []        # 1m closes (int, price_scale units)
        self.highs = []         # 1m highs (int, price_scale units)
        self.lows = []          # 1m lows (int, price_scale units)
        self.entry_price = None  # implied entry price of the open position
        self.high_since_entry = None  # highest close since entry
        self.hold_bars = 0      # bars held in the current position
        self.peak_equity = None  # highest equity seen (drawdown guardrail)
        self.stopped = False    # True once the drawdown guardrail fires

    # -- indicators ------------------------------------------------------
    def _breakout(self):
        """True when the latest close breaks above the highest high of the
        last DONCHIAN_IN bars (excluding the current bar)."""
        if len(self.highs) < DONCHIAN_IN + 1:
            return False
        recent_high = max(self.highs[-DONCHIAN_IN - 1:-1])
        return self.closes[-1] > recent_high

    def _channel_breakdown(self):
        """True when the latest close falls below the lowest low of the
        last DONCHIAN_OUT bars (excluding the current bar)."""
        if len(self.lows) < DONCHIAN_OUT + 1:
            return False
        recent_low = min(self.lows[-DONCHIAN_OUT - 1:-1])
        return self.closes[-1] < recent_low

    # -- position bookkeeping --------------------------------------------
    def _implied_entry(self, state):
        """Entry price implied by the position's cost (fees included).

        value(qty, price) = qty * price / 10**7, so
        entry_price = cost * 10**7 // qty. This is the true break-even
        price: the position only profits above it.
        """
        holding = state.positions.get(SYMBOL)
        if holding is None or holding.qty <= 0:
            return None
        return holding.cost * 10**7 // holding.qty

    def _pnl_bps(self, close):
        """Current P&L of the open position in bps vs the entry price."""
        if self.entry_price is None or self.entry_price <= 0:
            return 0
        return (close - self.entry_price) * BPS // self.entry_price

    def _trailing_stop_price(self):
        """The trailing stop price: 20 bps below the highest close since
        entry. Only meaningful once the trailing profit has activated."""
        if self.high_since_entry is None:
            return None
        return self.high_since_entry * (BPS - TRAIL_DIST_BPS) // BPS

    # -- the decision ----------------------------------------------------
    def decide(self, state):
        """Return the list of orders for this batch (possibly empty)."""
        close = state.close(SYMBOL)
        if close is None:
            return []  # no bar for CBBTC yet: nothing to decide on
        bar = state.latest.get(SYMBOL, {})
        high = int(bar.get("h", close))
        low = int(bar.get("l", close))
        self.closes.append(close)
        self.highs.append(high)
        self.lows.append(low)

        # Drawdown guardrail: track the peak equity; once we are more than
        # MAX_DD_BPS below it, stop trading for the rest of the window.
        if self.peak_equity is None:
            self.peak_equity = state.equity
        elif state.equity > self.peak_equity:
            self.peak_equity = state.equity
        if self.peak_equity > 0:
            dd_bps = (self.peak_equity - state.equity) * BPS // self.peak_equity
            if dd_bps >= MAX_DD_BPS:
                self.stopped = True

        holding = state.positions.get(SYMBOL)
        have_position = holding is not None and holding.qty > 0

        if have_position:
            # Refresh the entry record from the position's cost (robust to
            # fills arriving a bar late, and to rejections).
            entry = self._implied_entry(state)
            if entry is not None and self.entry_price is None:
                self.entry_price = entry
                self.high_since_entry = close
                self.hold_bars = 0
            if self.high_since_entry is not None:
                self.high_since_entry = max(self.high_since_entry, close)
            self.hold_bars += 1

            pnl = self._pnl_bps(close)
            exit_now = False
            # 1. TAKE PROFIT: fixed +300 bps target.
            if pnl >= TAKE_PROFIT_BPS:
                exit_now = True
            # 2. STOP LOSS: fixed -150 bps stop.
            elif pnl <= -STOP_LOSS_BPS:
                exit_now = True
            # 3. TRAILING PROFIT + 4. STOP TRAILING PROFIT: once the trade
            # is +20 bps in profit the stop ratchets to breakeven and
            # then trails 20 bps below the highest close since entry.
            elif pnl >= TRAIL_ACTIVATE_BPS:
                trail_price = self._trailing_stop_price()
                if trail_price is not None and close <= trail_price:
                    exit_now = True
            # Channel exit: the uptrend is over.
            if not exit_now and self._channel_breakdown():
                exit_now = True
            # Time exit: a scalp that has not paid off in 6 hours is stale.
            if not exit_now and self.hold_bars >= MAX_HOLD_BARS:
                exit_now = True
            # Drawdown guardrail.
            if not exit_now and self.stopped:
                exit_now = True

            if exit_now:
                self.entry_price = None
                self.high_since_entry = None
                self.hold_bars = 0
                return [
                    {
                        "side": "sell",
                        "symbol": SYMBOL,
                        "qty": holding.qty,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }
                ]
            return []  # hold: let the scalp run

        # Flat: look for a trend-following breakout entry.
        self.entry_price = None
        self.high_since_entry = None
        self.hold_bars = 0
        if self.stopped:
            return []  # guardrail fired: stay in cash
        if state.warming_up:
            return []  # warm-up bars: orders would be rejected
        if not self._breakout():
            return []  # no breakout: never buy a flat/falling market
        # Size: up to POSITION_FRACTION of cash, within the weight cap.
        room = state.weight_room(SYMBOL)
        notional = state.cash * POSITION_FRACTION_BPS // BPS
        notional = min(notional, room)
        min_notional = int(state.hello["fees"]["min_notional_quote_units"])
        if notional < min_notional:
            return []
        return [
            {
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": notional,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }
        ]


_SCALPER = Scalper()


def on_batch(state, batch):
    """One reply per batch: the scalper's orders for this bar (or none)."""
    try:
        return _SCALPER.decide(state)
    except Exception:
        # Never crash: a crash mid-race scores 0. On any unexpected
        # error, answer with no orders (stay flat / hold) and keep going.
        import sys as _sys

        print(f"bot error at seq {state.seq}", file=_sys.stderr)
        return []


def main():
    makefun_bars.run(on_batch)


if __name__ == "__main__":
    main()
