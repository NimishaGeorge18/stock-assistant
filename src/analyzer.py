import ta
import pandas as pd
from datetime import datetime

def calculate_indicators(df: pd.DataFrame) -> dict:
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # RSI
    rsi = ta.momentum.RSIIndicator(close=close, window=14)
    rsi_value = round(float(rsi.rsi().iloc[-1]), 2)

    # MACD
    macd = ta.trend.MACD(close=close)
    macd_line = float(macd.macd().iloc[-1])
    signal_line = float(macd.macd_signal().iloc[-1])
    macd_prev = float(macd.macd().iloc[-2])
    signal_prev = float(macd.macd_signal().iloc[-2])
    macd_crossover = macd_prev < signal_prev and macd_line > signal_line
    macd_crossunder = macd_prev > signal_prev and macd_line < signal_line

    # EMA trend
    ema20 = ta.trend.EMAIndicator(close=close, window=20)
    ema50 = ta.trend.EMAIndicator(close=close, window=50)
    ema20_val = float(ema20.ema_indicator().iloc[-1])
    ema50_val = float(ema50.ema_indicator().iloc[-1])
    uptrend = ema20_val > ema50_val

    # Volume
    avg_volume = float(volume.rolling(20).mean().iloc[-1])
    current_volume = float(volume.iloc[-1])
    vol_surge = current_volume > avg_volume * 1.3

    return {
        "rsi": rsi_value,
        "macd_crossover": macd_crossover,
        "macd_crossunder": macd_crossunder,
        "uptrend": uptrend,
        "vol_surge": vol_surge,
        "current_price": round(float(close.iloc[-1]), 2),
        "high_5d": round(float(high.iloc[-5:].max()), 2),
        "low_5d": round(float(low.iloc[-5:].min()), 2),
    }

def analyze_stock(stock_data: dict, df=None) -> dict:
    price = stock_data["current_price"]
    high = stock_data["high_5d"]
    low = stock_data["low_5d"]
    range_5d = high - low if (high - low) > 0 else 1

    # default fallback without indicators
    ind = None
    if df is not None and len(df) >= 50:
        try:
            ind = calculate_indicators(df)
        except Exception as e:
            print(f"Indicator error: {e}")

    if ind:
        rsi = ind["rsi"]
        # strong BUY: RSI oversold + MACD crossover + uptrend
        if rsi < 35 and ind["macd_crossover"] and ind["uptrend"]:
            signal = "BUY"
            reason = f"RSI oversold ({rsi}) + MACD bullish crossover + uptrend"
        # moderate BUY: RSI oversold + volume surge
        elif rsi < 30 and ind["vol_surge"]:
            signal = "BUY"
            reason = f"RSI oversold ({rsi}) with volume surge"
        # strong SELL: RSI overbought + MACD crossunder
        elif rsi > 65 and ind["macd_crossunder"]:
            signal = "SELL"
            reason = f"RSI overbought ({rsi}) + MACD bearish crossover"
        # moderate SELL: RSI very overbought
        elif rsi > 75:
            signal = "SELL"
            reason = f"RSI very overbought ({rsi})"
        else:
            signal = "HOLD"
            reason = f"RSI neutral ({rsi}) — no clear signal"
    else:
        # fallback to simple logic
        position = (price - low) / range_5d
        if position < 0.35:
            signal = "BUY"
            reason = "Price near 5-day low"
        elif position > 0.75:
            signal = "SELL"
            reason = "Price near 5-day high"
        else:
            signal = "HOLD"
            reason = "Price in middle of range"

    # calculate entry, SL, target
    atr = range_5d * 0.1  # simple ATR approximation
    if signal == "BUY":
        entry = price
        stop_loss = round(entry - atr * 1.5, 2)
        target = round(entry + atr * 3, 2)
    elif signal == "SELL":
        entry = price
        stop_loss = round(entry + atr * 1.5, 2)
        target = round(entry - atr * 3, 2)
    else:
        entry = price
        stop_loss = round(price - atr, 2)
        target = round(price + atr * 2, 2)

    result = {
        "stock": stock_data["stock"],
        "signal": signal,
        "entry": round(entry, 2),
        "stop_loss": stop_loss,
        "target": target,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    print(f"\n{result['stock']}: {result['signal']}")
    print(f"  Entry:     ₹{result['entry']}")
    print(f"  Target:    ₹{result['target']}")
    print(f"  Stop Loss: ₹{result['stop_loss']}")
    print(f"  Reason:    {result['reason']}")

    return result

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
    print("\nAnalyzing...\n")
    analyze_all(stocks)