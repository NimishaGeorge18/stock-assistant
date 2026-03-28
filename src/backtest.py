import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

STOCKS = {
    "ITC": "ITC.NS",
    "RELIANCE": "RELIANCE.NS",
    "ONGC": "ONGC.NS"
}

def get_historical_data(symbol: str, months: int = 6) -> pd.DataFrame:
    end = datetime.now()
    start = end - timedelta(days=months * 30)
    df = yf.download(symbol, start=start, end=end, interval="1d", progress=False)
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    return df

def generate_signal(df_window: pd.DataFrame, current_row) -> dict:
    try:
        import ta
        close = df_window["Close"]
        high = df_window["High"]
        low = df_window["Low"]
        volume = df_window["Volume"]

        if len(close) < 50:
            return None

        rsi = ta.momentum.RSIIndicator(close=close, window=14)
        rsi_val = float(rsi.rsi().iloc[-1])

        if pd.isna(rsi_val):
            return None

        # trend
        ema20 = float(ta.trend.EMAIndicator(close=close, window=20).ema_indicator().iloc[-1])
        ema50 = float(ta.trend.EMAIndicator(close=close, window=50).ema_indicator().iloc[-1])
        uptrend = ema20 > ema50
        downtrend = ema20 < ema50

        # MACD
        macd = ta.trend.MACD(close=close)
        macd_line = float(macd.macd().iloc[-1])
        signal_line = float(macd.macd_signal().iloc[-1])

        price = float(current_row["Close"])
        high_5d = float(high.iloc[-5:].max())
        low_5d = float(low.iloc[-5:].min())
        range_5d = high_5d - low_5d if (high_5d - low_5d) > 0 else 1
        atr = range_5d * 0.1

        # BUY: RSI oversold + either uptrend OR MACD positive
        if rsi_val < 35 and (uptrend or macd_line > signal_line):
            signal = "BUY"
        # SELL: RSI overbought + either downtrend OR MACD negative
        elif rsi_val > 65 and (downtrend or macd_line < signal_line):
            signal = "SELL"
        else:
            return None

        if signal == "BUY":
            entry = price
            stop_loss = round(entry - atr * 1.5, 2)
            target = round(entry + atr * 3, 2)
        else:
            entry = price
            stop_loss = round(entry + atr * 1.5, 2)
            target = round(entry - atr * 3, 2)

        return {
            "signal": signal,
            "entry": round(entry, 2),
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2)
        }

    except Exception as e:
        return None
    
def check_outcome(signal: dict, future_prices: pd.Series) -> str:
    entry = signal["entry"]
    target = signal["target"]
    stop_loss = signal["stop_loss"]

    for price in future_prices:
        price = float(price)
        if signal["signal"] == "BUY":
            if price >= target:
                return "WIN"
            if price <= stop_loss:
                return "LOSS"
        elif signal["signal"] == "SELL":
            if price <= target:
                return "WIN"
            if price >= stop_loss:
                return "LOSS"

    return "OPEN"

def backtest_stock(stock_name: str, months: int = 6) -> dict:
    symbol = STOCKS[stock_name]
    print(f"\nBacktesting {stock_name}...")

    df = get_historical_data(symbol, months)

    if df.empty or len(df) < 20:
        print(f"Not enough data for {stock_name}")
        return None

    trades = []

    for i in range(20, len(df) - 5):
        window = df.iloc[:i]
        row = df.iloc[i]
        future = df.iloc[i+1:i+6]["Close"]

        signal = generate_signal(window, row)
        if signal is None:
            continue

        outcome = check_outcome(signal, future)
        if outcome == "OPEN":
            continue

        pnl = 0
        if outcome == "WIN":
            if signal["signal"] == "BUY":
                pnl = signal["target"] - signal["entry"]
            else:
                pnl = signal["entry"] - signal["target"]
        else:
            if signal["signal"] == "BUY":
                pnl = signal["stop_loss"] - signal["entry"]
            else:
                pnl = signal["entry"] - signal["stop_loss"]

        trades.append({
            "date": str(df.index[i].date()),
            "signal": signal["signal"],
            "entry": signal["entry"],
            "target": signal["target"],
            "stop_loss": signal["stop_loss"],
            "outcome": outcome,
            "pnl": round(pnl, 2)
        })

    if not trades:
        print(f"No trades generated for {stock_name}")
        return None

    wins = [t for t in trades if t["outcome"] == "WIN"]
    losses = [t for t in trades if t["outcome"] == "LOSS"]
    total_pnl = round(sum(t["pnl"] for t in trades), 2)
    win_rate = round(len(wins) / len(trades) * 100, 1) if trades else 0
    avg_win = round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0
    avg_loss = round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0

    return {
        "stock": stock_name,
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "total_pnl": total_pnl,
        "trades": trades
    }

def print_report(results: list):
    print("\n" + "="*50)
    print("BACKTEST REPORT — Last 6 months")
    print("="*50)

    overall_pnl = 0
    overall_trades = 0
    overall_wins = 0

    for r in results:
        if not r:
            continue

        overall_pnl += r["total_pnl"]
        overall_trades += r["total_trades"]
        overall_wins += r["wins"]

        print(f"\n{r['stock']}")
        print(f"  Total trades:  {r['total_trades']}")
        print(f"  Wins:          {r['wins']}")
        print(f"  Losses:        {r['losses']}")
        print(f"  Win rate:      {r['win_rate']}%")
        print(f"  Avg win:       ₹{r['avg_win']}")
        print(f"  Avg loss:      ₹{r['avg_loss']}")
        print(f"  Total P&L:     ₹{r['total_pnl']}")

        print(f"\n  Recent trades:")
        for t in r["trades"][-5:]:
            icon = "✅" if t["outcome"] == "WIN" else "❌"
            print(f"  {icon} {t['date']} {t['signal']} "
                  f"₹{t['entry']} → ₹{t['target']} "
                  f"P&L: ₹{t['pnl']}")

    print("\n" + "="*50)
    if overall_trades > 0:
        overall_win_rate = round(overall_wins / overall_trades * 100, 1)
        print(f"OVERALL")
        print(f"  Total trades:  {overall_trades}")
        print(f"  Win rate:      {overall_win_rate}%")
        print(f"  Total P&L:     ₹{round(overall_pnl, 2)}")

        if overall_win_rate >= 55:
            print("\n  Strategy looks GOOD — win rate above 55%")
        elif overall_win_rate >= 45:
            print("\n  Strategy is AVERAGE — consider tuning")
        else:
            print("\n  Strategy needs IMPROVEMENT — win rate too low")
    print("="*50)

if __name__ == "__main__":
    print("Running backtest on last 6 months of data...")
    results = []
    for stock in STOCKS:
        result = backtest_stock(stock)
        results.append(result)
    print_report(results)