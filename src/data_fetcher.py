import yfinance as yf
from datetime import datetime

# Stock symbols — yfinance uses .NS suffix for NSE stocks
STOCKS = {
    "ITC": "ITC.NS",
    "RELIANCE": "RELIANCE.NS",
    "ONGC": "ONGC.NS"
}

def get_stock_data(stock_name: str) -> dict:
    symbol = STOCKS[stock_name]
    ticker = yf.Ticker(symbol)
    
    # get last 5 days of hourly data
    hist = ticker.history(period="5d", interval="1h")
    
    if hist.empty:
        raise ValueError(f"No data returned for {symbol}")
    
    latest = hist.iloc[-1]
    prev = hist.iloc[-2]
    
    current_price = round(float(latest["Close"]), 2)
    prev_price = round(float(prev["Close"]), 2)
    change_pct = round(((current_price - prev_price) / prev_price) * 100, 2)
    
    high_5d = round(float(hist["High"].max()), 2)
    low_5d = round(float(hist["Low"].min()), 2)
    avg_volume = round(float(hist["Volume"].mean()), 0)
    current_volume = round(float(latest["Volume"]), 0)
    
    return {
        "stock": stock_name,
        "symbol": symbol,
        "current_price": current_price,
        "change_pct": change_pct,
        "high_5d": high_5d,
        "low_5d": low_5d,
        "avg_volume": avg_volume,
        "current_volume": current_volume,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_all_stocks() -> list:
    results = []
    for stock_name in STOCKS:
        try:
            data = get_stock_data(stock_name)
            print(f"{stock_name}: ₹{data['current_price']} ({data['change_pct']}%)")
            results.append(data)
        except Exception as e:
            print(f"ERROR fetching {stock_name}: {e}")
    return results

# NOTE: When you get Kite Connect API key, replacing yfinance is just this:
# kite.ltp(f"NSE:{symbol}")["NSE:{symbol}"]["last_price"]

if __name__ == "__main__":
    print("Fetching stock data...\n")
    get_all_stocks()