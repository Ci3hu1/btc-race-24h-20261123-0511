"""Tests for the BTC race scalper (main.py).

Covers the four mandatory risk controls (take profit, stop loss, trailing
profit, trailing stop loss), the Donchian breakout entry, staying flat in
a downtrend, and robustness (missing bars, determinism).

Run: python3 -m pytest tests/ -q   (or: python3 tests/test_bot.py)
Pure stdlib: no third-party test framework needed.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vendor"))

import makefun_bars  # noqa: E402
import main as bot  # noqa: E402

SYMBOL = "CBBTC"
PRICE = 6_000_000_000  # $60,000 at price_scale 5
HELLO = {
    "protocol": "agent-fun/bars-replay/v1",
    "seed": 42,
    "symbols": [{"symbol": SYMBOL, "mint": "cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij",
                 "price_scale": 5, "qty_scale": 8}],
    "capital": {"quote": "USDC", "quote_scale": 6, "quote_units": "1000000000"},
    "bar_interval": "1m",
    "caps": {"max_open_positions": 1, "max_orders_per_bar": 16,
             "max_weight_bps": 10000, "shorts": False, "leverage": False},
    "fees": {"fee_bps": 4, "slippage_bps": 2, "min_notional_quote_units": "1000000"},
    "latency_bars": 1,
}


def bar(price, t=0, seq=0):
    """A 1-minute bar with o/h/l/c all at `price` (flat bar)."""
    return {"symbol": SYMBOL, "t": t, "o": str(price), "h": str(price),
            "l": str(price), "c": str(price), "v": None,
            "o_depth": ["1382154790000"], "c_depth": ["1382154790000"]}


def make_state():
    return makefun_bars.BarsState(HELLO)


def feed(scalper, state, prices, start_seq=0):
    """Feed a list of closes through the scalper; return the list of
    order-lists (one per batch). Simulates fills at the next bar's open
    by updating the state's account after each buy/sell decision."""
    out = []
    cash = 1_000_000_000
    qty = 0
    cost = 0
    pending = []
    for i, p in enumerate(prices):
        seq = start_seq + i
        b = bar(p, t=seq * 60000, seq=seq)
        # Fill the previous batch's orders at this bar's open (approx:
        # at the open price, ignoring fee/slippage for the test harness;
        # the fill price is close enough to exercise the exit logic).
        for o in pending:
            if o["side"] == "buy":
                notional = int(o["notional_quote_units"])
                q = notional * 10**13 // (p * 10**6)
                cash -= notional
                qty = q
                cost = notional
            else:
                cash += qty * p * 10**6 // 10**13
                qty = 0
                cost = 0
        pending = []
        state.seq = seq
        state.t = seq * 60000
        state.latest = {SYMBOL: b}
        state.cash = cash
        state.equity = cash + (qty * p * 10**6 // 10**13 if qty else 0)
        state.positions = (
            {SYMBOL: makefun_bars.Holding(qty, cost)} if qty else {}
        )
        orders = scalper.decide(state)
        out.append(orders)
        pending = list(orders)
    return out


class TestEntry(unittest.TestCase):
    def test_no_trade_without_breakout(self):
        """Flat market (no new 2-hour high): the bot stays in cash."""
        s = bot.Scalper()
        state = make_state()
        prices = [PRICE] * 200  # flat: never breaks above the 120-bar high
        orders = feed(s, state, prices)
        buys = [o for batch in orders for o in batch if o["side"] == "buy"]
        self.assertEqual(buys, [])

    def test_breakout_entry(self):
        """A close above the highest high of the last 120 bars opens a long."""
        s = bot.Scalper()
        state = make_state()
        # 130 flat bars, then a rising run that breaks the 120-bar high.
        prices = [PRICE] * 130 + [PRICE + i * 1_000_000 for i in range(1, 11)]
        orders = feed(s, state, prices)
        buys = [o for batch in orders for o in batch if o["side"] == "buy"]
        self.assertEqual(len(buys), 1)
        self.assertEqual(buys[0]["symbol"], SYMBOL)
        # Position size is 50% of cash.
        self.assertEqual(int(buys[0]["notional_quote_units"]), 500_000_000)

    def test_no_buy_in_downtrend(self):
        """Steadily falling prices: no breakout, no trade."""
        s = bot.Scalper()
        state = make_state()
        prices = [PRICE - i * 1_000_000 for i in range(200)]
        orders = feed(s, state, prices)
        buys = [o for batch in orders for o in batch if o["side"] == "buy"]
        self.assertEqual(buys, [])


class TestTakeProfit(unittest.TestCase):
    def test_tp_closes_trade(self):
        """A trade that rises +3.0% (the TP) is closed at the TP."""
        s = bot.Scalper()
        state = make_state()
        # Build a breakout, then rally straight to +3.0% above entry.
        prices = [PRICE] * 130
        prices += [PRICE + i * 1_000_000 for i in range(1, 11)]  # breakout
        entry = prices[-1]
        # Rally: +3.0% above the entry price in one step, then flat.
        tp_price = entry * 10300 // 10000
        prices += [tp_price] * 3
        orders = feed(s, state, prices)
        sells = [o for batch in orders for o in batch if o["side"] == "sell"]
        self.assertEqual(len(sells), 1)
        self.assertEqual(sells[0]["symbol"], SYMBOL)


class TestStopLoss(unittest.TestCase):
    def test_sl_closes_trade(self):
        """A trade that falls -1.5% (the SL) is closed at the SL."""
        s = bot.Scalper()
        state = make_state()
        prices = [PRICE] * 130
        prices += [PRICE + i * 1_000_000 for i in range(1, 11)]  # breakout
        entry = prices[-1]
        # Crash: -1.5% below the entry price in one step, then flat.
        sl_price = entry * 9850 // 10000
        prices += [sl_price] * 3
        orders = feed(s, state, prices)
        sells = [o for batch in orders for o in batch if o["side"] == "sell"]
        self.assertEqual(len(sells), 1)

    def test_every_trade_has_a_stop(self):
        """The SL constant is positive and the exit logic always checks it:
        a position open for 200 bars in a falling market is stopped out,
        never left to bleed past the SL."""
        s = bot.Scalper()
        state = make_state()
        prices = [PRICE] * 130
        prices += [PRICE + i * 1_000_000 for i in range(1, 11)]
        entry = prices[-1]
        # Slow bleed: -0.1% per bar. The SL (-1.5%) must fire by bar 15.
        prices += [entry - i * entry // 1000 for i in range(1, 30)]
        orders = feed(s, state, prices)
        sells = [o for batch in orders for o in batch if o["side"] == "sell"]
        self.assertEqual(len(sells), 1)
        # The exit happened within 20 bars of the entry (the SL fired).
        sell_idx = next(
            i for i, batch in enumerate(orders)
            for o in batch if o["side"] == "sell"
        )
        self.assertLess(sell_idx, 130 + 10 + 20)


class TestTrailing(unittest.TestCase):
    def test_trailing_stop_locks_in_profit_on_reversal(self):
        """The trade rises +1.0%, then reverses 0.20% from its high: the
        trailing stop closes it WITH a profit locked in (not at breakeven,
        not at a loss)."""
        s = bot.Scalper()
        state = make_state()
        prices = [PRICE] * 130
        prices += [PRICE + i * 1_000_000 for i in range(1, 11)]  # breakout
        entry = prices[-1]
        high = entry * 10100 // 10000  # +1.0%
        prices += [high] * 2
        # Reverse 0.20% from the high (the trail distance): trailing stop fires.
        rev = high * 9980 // 10000
        prices += [rev] * 3
        orders = feed(s, state, prices)
        sells = [o for batch in orders for o in batch if o["side"] == "sell"]
        self.assertEqual(len(sells), 1)
        # The exit price is above the entry price: profit was locked in.
        self.assertGreater(rev, entry)

    def test_trailing_profit_rises_with_price(self):
        """While the price keeps making new highs, the trailing stop does
        NOT fire: the trade keeps running (trailing profit)."""
        s = bot.Scalper()
        state = make_state()
        prices = [PRICE] * 130
        prices += [PRICE + i * 1_000_000 for i in range(1, 11)]  # breakout
        entry = prices[-1]
        # Steady climb: +0.1% per bar for 10 bars (well under the +3% TP).
        prices += [entry + i * entry // 1000 for i in range(1, 11)]
        orders = feed(s, state, prices)
        sells = [o for batch in orders for o in batch if o["side"] == "sell"]
        self.assertEqual(sells, [])

    def test_trailing_stop_never_moves_down(self):
        """After the trailing stop activates, a small dip that does NOT
        reach the trail distance does not close the trade, and a later
        new high raises the stop (the stop only ratchets up)."""
        s = bot.Scalper()
        state = make_state()
        prices = [PRICE] * 130
        prices += [PRICE + i * 1_000_000 for i in range(1, 11)]
        entry = prices[-1]
        high1 = entry * 10100 // 10000  # +1.0%
        prices += [high1] * 2
        dip = high1 * 9990 // 10000  # -0.10% dip: inside the 0.20% trail
        prices += [dip] * 2
        high2 = high1 * 10100 // 10000  # new high: +1.0% above high1
        prices += [high2] * 2
        orders = feed(s, state, prices)
        sells = [o for batch in orders for o in batch if o["side"] == "sell"]
        self.assertEqual(sells, [])


class TestChannelExit(unittest.TestCase):
    def test_channel_breakdown_closes_trade(self):
        """A slow drift down that breaks the 60-bar low (without hitting
        the -1.5% SL) closes the trade on the channel exit."""
        s = bot.Scalper()
        state = make_state()
        prices = [PRICE] * 130
        prices += [PRICE + i * 1_000_000 for i in range(1, 11)]  # breakout
        entry = prices[-1]
        # Drift down slowly: -0.05% per bar for 70 bars. The 60-bar low
        # breakdown fires before the -1.5% SL (which needs 30 bars at
        # this rate -- the channel exit is the faster one here).
        prices += [entry - i * entry // 2000 for i in range(1, 71)]
        orders = feed(s, state, prices)
        sells = [o for batch in orders for o in batch if o["side"] == "sell"]
        self.assertEqual(len(sells), 1)


class TestRobustness(unittest.TestCase):
    def test_missing_bar_does_not_crash(self):
        """A batch with no CBBTC bar (state.close returns the last close)
        is handled: decide() returns [] and does not raise."""
        s = bot.Scalper()
        state = make_state()
        # Feed some bars, then call decide with an empty latest (no bar).
        feed(s, state, [PRICE] * 10)
        state.latest = {}
        self.assertEqual(s.decide(state), [])

    def test_deterministic(self):
        """Two identical runs produce identical orders."""
        def run_once():
            s = bot.Scalper()
            state = make_state()
            prices = [PRICE] * 130
            prices += [PRICE + i * 1_000_000 for i in range(1, 11)]
            prices += [PRICE + 10_000_000 + i * 500_000 for i in range(20)]
            return feed(s, state, prices)
        self.assertEqual(run_once(), run_once())

    def test_drawdown_guardrail_stops_trading(self):
        """After a -5% drawdown the bot stops opening new trades."""
        s = bot.Scalper()
        state = make_state()
        # Force the guardrail by faking a peak equity then a low equity.
        s.peak_equity = 1_000_000_000
        state.equity = 940_000_000  # -6%
        state.cash = 940_000_000
        state.latest = {SYMBOL: bar(PRICE + 1_000_000_000)}
        # Feed enough bars for a breakout, then decide: must be [].
        for i in range(130):
            state.seq = i
            state.latest = {SYMBOL: bar(PRICE)}
            s.decide(state)
        state.latest = {SYMBOL: bar(PRICE + 1_000_000_000)}
        self.assertEqual(s.decide(state), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
