import ta
import pandas as pd
from datetime import datetime

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    vwap = (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()
    return vwap

def get_signal(df: pd.DataFrame) -> dict:
    if len(df) < 20:
        return None

    df = df.copy()
    close = df["Close"].squeeze()
    volume = df["Volume"].squeeze()

    # calculate VWAP
    df["vwap"] = calculate_vwap(df)

    # calculate RSI
    df["rsi"] = ta.momentum.RSIIndicator(
        close=close, window=14
    ).rsi()

    # volume average
    df["avg_volume"] = volume.rolling(20).mean()

    # get current and previous values
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(curr["Close"])
    vwap = float(curr["vwap"])
    rsi = float(curr["rsi"])
    prev_price = float(prev["Close"])
    prev_vwap = float(prev["vwap"])
    curr_vol = float(curr["Volume"])
    avg_vol = float(curr["avg_volume"])

    if pd.isna(rsi) or pd.isna(vwap):
        return None

    # ATR for stop loss and target
    recent = df.iloc[-10:]
    atr = float(
        (recent["High"].squeeze() - recent["Low"].squeeze()).mean()
    )
    if atr == 0:
        return None

    vol_surge = curr_vol > avg_vol * 1.2

    # VWAP crossover UP + RSI > 50 = BUY
    price_crossed_above = prev_price < prev_vwap and price > vwap
    # VWAP crossover DOWN + RSI < 50 = SELL
    price_crossed_below = prev_price > prev_vwap and price < vwap

    if price_crossed_above and rsi > 50 and vol_surge:
        signal = "BUY"
        reason = (
            f"Price crossed above VWAP ₹{round(vwap, 2)} "
            f"with RSI {round(rsi, 1)} and volume surge"
        )
    elif price_crossed_below and rsi < 50 and vol_surge:
        signal = "SELL"
        reason = (
            f"Price crossed below VWAP ₹{round(vwap, 2)} "
            f"with RSI {round(rsi, 1)} and volume surge"
        )
    else:
        signal = "HOLD"
        reason = (
            f"Price ₹{price} vs VWAP ₹{round(vwap, 2)}, "
            f"RSI {round(rsi, 1)} — no crossover"
        )

    # calculate entry, SL, target
    if signal == "BUY":
        entry = price
        stop_loss = round(vwap - atr, 2)
        risk = entry - stop_loss
        target = round(entry + risk * 2, 2)
    elif signal == "SELL":
        entry = price
        stop_loss = round(vwap + atr, 2)
        risk = stop_loss - entry
        target = round(entry - risk * 2, 2)
    else:
        entry = price
        stop_loss = round(price - atr, 2)
        target = round(price + atr * 2, 2)

    return {
        "stock": "",
        "signal": signal,
        "entry": round(entry, 2),
        "stop_loss": stop_loss,
        "target": target,
        "vwap": round(vwap, 2),
        "rsi": round(rsi, 1),
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def analyze_stock(stock_data: dict, df: pd.DataFrame = None) -> dict:
    price = stock_data["current_price"]

    if df is not None and len(df) >= 20:
        result = get_signal(df)
        if result:
            result["stock"] = stock_data["stock"]
            print(f"\n{result['stock']}: {result['signal']}")
            print(f"  Price:     ₹{price}")
            print(f"  VWAP:      ₹{result['vwap']}")
            print(f"  RSI:       {result['rsi']}")
            print(f"  Entry:     ₹{result['entry']}")
            print(f"  Target:    ₹{result['target']}")
            print(f"  Stop Loss: ₹{result['stop_loss']}")
            print(f"  Reason:    {result['reason']}")
            return result

    # fallback if no df passed
    atr = (stock_data["high_5d"] - stock_data["low_5d"]) * 0.1
    return {
        "stock": stock_data["stock"],
        "signal": "HOLD",
        "entry": price,
        "stop_loss": round(price - atr, 2),
        "target": round(price + atr * 2, 2),
        "vwap": 0,
        "rsi": 0,
        "reason": "Insufficient intraday data",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def analyze_all(stocks_data: list) -> list:
    results = []
    for stock_data in stocks_data:
        try:
            result = analyze_stock(stock_data)
            results.append(result)
        except Exception as e:
            print(f"ERROR analyzing {stock_data['stock']}: {e}")
    return results

if __name__ == "__main__":
    from data_fetcher import get_all_stocks
    print("Fetching data...\n")
    stocks = get_all_stocks()
    print("\nAnalyzing with VWAP + RSI...\n")
    analyze_all(stocks)