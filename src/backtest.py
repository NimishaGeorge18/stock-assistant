import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta

STOCKS = {
    "ITC": "ITC.NS",
    "RELIANCE": "RELIANCE.NS",
    "ONGC": "ONGC.NS"
}

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    return (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()

def get_intraday_data(symbol: str) -> pd.DataFrame:
    end = datetime.now()
    start = end - timedelta(days=57)
    df = yf.download(
        symbol,
        start=start,
        end=end,
        interval="5m",
        progress=False
    )
    df.columns = [
        col[0] if isinstance(col, tuple) else col
        for col in df.columns
    ]
    df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("Asia/Kolkata")
    df = df.between_time("09:15", "15:30")
    return df

def run_vwap_rsi_backtest(df: pd.DataFrame) -> list:
    trades = []

    # group by day — VWAP resets every day
    df["date"] = df.index.date
    days = df["date"].unique()

    for day in days:
        day_df = df[df["date"] == day].copy()

        if len(day_df) < 20:
            continue

        close = day_df["Close"].squeeze()
        volume = day_df["Volume"].squeeze()

        # VWAP for this day
        typical = (
            day_df["High"].squeeze() +
            day_df["Low"].squeeze() +
            close
        ) / 3
        day_df["vwap"] = (
            (typical * volume).cumsum() / volume.cumsum()
        )

        # RSI
        day_df["rsi"] = ta.momentum.RSIIndicator(
            close=close, window=14
        ).rsi()

        # volume average
        day_df["avg_vol"] = volume.rolling(10).mean()

        in_trade = False

        for i in range(1, len(day_df)):
            if in_trade:
                continue

            curr = day_df.iloc[i]
            prev = day_df.iloc[i-1]

            price = float(curr["Close"])
            vwap = float(curr["vwap"])
            rsi = float(curr["rsi"])
            prev_price = float(prev["Close"])
            prev_vwap = float(prev["vwap"])
            curr_vol = float(curr["Volume"])
            avg_vol = float(curr["avg_vol"])

            if pd.isna(rsi) or pd.isna(vwap):
                continue

            vol_surge = curr_vol > avg_vol * 1.2

            # ATR
            recent = day_df.iloc[max(0, i-10):i]
            atr = float(
                (
                    recent["High"].squeeze() -
                    recent["Low"].squeeze()
                ).mean()
            )
            if atr == 0:
                continue

            crossed_above = prev_price < prev_vwap and price > vwap
            crossed_below = prev_price > prev_vwap and price < vwap

            signal = None
            if crossed_above and rsi > 50 and vol_surge:
                signal = "BUY"
                entry = price
                stop_loss = round(vwap - atr, 2)
                risk = entry - stop_loss
                target = round(entry + risk * 2, 2)
            elif crossed_below and rsi < 50 and vol_surge:
                signal = "SELL"
                entry = price
                stop_loss = round(vwap + atr, 2)
                risk = stop_loss - entry
                target = round(entry - risk * 2, 2)

            if not signal:
                continue

            # check outcome in remaining candles of that day
            future = day_df.iloc[i+1:]
            outcome = "OPEN"
            pnl = 0

            for _, f in future.iterrows():
                h = float(f["High"])
                l = float(f["Low"])

                if signal == "BUY":
                    if h >= target:
                        outcome = "WIN"
                        pnl = round(target - entry, 2)
                        break
                    if l <= stop_loss:
                        outcome = "LOSS"
                        pnl = round(stop_loss - entry, 2)
                        break
                elif signal == "SELL":
                    if l <= target:
                        outcome = "WIN"
                        pnl = round(entry - target, 2)
                        break
                    if h >= stop_loss:
                        outcome = "LOSS"
                        pnl = round(entry - stop_loss, 2)
                        break

            if outcome == "OPEN":
                continue

            in_trade = True
            trades.append({
                "date": str(day),
                "signal": signal,
                "entry": round(entry, 2),
                "target": round(target, 2),
                "stop_loss": round(stop_loss, 2),
                "vwap": round(vwap, 2),
                "rsi": round(rsi, 1),
                "outcome": outcome,
                "pnl": pnl
            })

    return trades

def print_report(stock_name: str, trades: list):
    if not trades:
        print(f"\n{stock_name}: No trades generated")
        return

    wins = [t for t in trades if t["outcome"] == "WIN"]
    losses = [t for t in trades if t["outcome"] == "LOSS"]
    win_rate = round(len(wins) / len(trades) * 100, 1)
    total_pnl = round(sum(t["pnl"] for t in trades), 2)
    avg_win = round(
        sum(t["pnl"] for t in wins) / len(wins), 2
    ) if wins else 0
    avg_loss = round(
        sum(t["pnl"] for t in losses) / len(losses), 2
    ) if losses else 0

    print(f"\n{stock_name}")
    print(f"  Total trades:  {len(trades)}")
    print(f"  Wins:          {len(wins)}")
    print(f"  Losses:        {len(losses)}")
    print(f"  Win rate:      {win_rate}%")
    print(f"  Avg win:       ₹{avg_win}")
    print(f"  Avg loss:      ₹{avg_loss}")
    print(f"  Total P&L:     ₹{total_pnl}")

    print(f"\n  Last 5 trades:")
    for t in trades[-5:]:
        icon = "✅" if t["outcome"] == "WIN" else "❌"
        print(
            f"  {icon} {t['date']} {t['signal']} "
            f"₹{t['entry']} VWAP:₹{t['vwap']} "
            f"RSI:{t['rsi']} P&L:₹{t['pnl']}"
        )

    return {
        "trades": len(trades),
        "wins": len(wins),
        "win_rate": win_rate,
        "total_pnl": total_pnl
    }

if __name__ == "__main__":
    print("VWAP + RSI Backtest — 5-min candles, last 60 days\n")
    print("="*55)

    all_trades = 0
    all_wins = 0
    all_pnl = 0

    for stock_name, symbol in STOCKS.items():
        print(f"Downloading {stock_name}...")
        df = get_intraday_data(symbol)
        print(f"  {len(df)} candles downloaded")

        trades = run_vwap_rsi_backtest(df)
        result = print_report(stock_name, trades)

        if result:
            all_trades += result["trades"]
            all_wins += result["wins"]
            all_pnl += result["total_pnl"]

    print("\n" + "="*55)
    print("OVERALL")
    if all_trades > 0:
        overall_wr = round(all_wins / all_trades * 100, 1)
        print(f"  Total trades:  {all_trades}")
        print(f"  Win rate:      {overall_wr}%")
        print(f"  Total P&L:     ₹{round(all_pnl, 2)}")

        if overall_wr >= 55:
            print("\n  Strategy GOOD — ready to go live ✅")
        elif overall_wr >= 45:
            print("\n  Strategy AVERAGE — needs tuning ⚠️")
        else:
            print("\n  Strategy POOR — do not go live ❌")
    print("="*55)