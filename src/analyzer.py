import json
from datetime import datetime

def analyze_stock(stock_data: dict) -> dict:
    price = stock_data["current_price"]
    high = stock_data["high_5d"]
    low = stock_data["low_5d"]
    change = stock_data["change_pct"]
    volume = stock_data["current_volume"]
    avg_vol = stock_data["avg_volume"]

    range_5d = high - low
    position = (price - low) / range_5d if range_5d > 0 else 0.5
    vol_surge = volume > avg_vol * 1.2

    if position < 0.35 and change > 0 and vol_surge:
        signal = "BUY"
        entry = price
        stop_loss = round(low - (range_5d * 0.05), 2)
        risk = entry - stop_loss
        target = round(entry + (risk * 2), 2)
        reason = "Price near 5-day low with volume surge and positive momentum"
    elif position > 0.75 and change < 0:
        signal = "SELL"
        entry = price
        stop_loss = round(high + (range_5d * 0.05), 2)
        risk = stop_loss - entry
        target = round(entry - (risk * 2), 2)
        reason = "Price near 5-day high with negative momentum"
    else:
        signal = "HOLD"
        entry = price
        stop_loss = round(price * 0.985, 2)
        target = round(price * 1.03, 2)
        reason = "No clear signal — price in middle of range"

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