import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

STOCKS = {
    "ITC": "ITC.NS",
    "RELIANCE": "RELIANCE.NS",
    "ONGC": "ONGC.NS"
}

IST = pytz.timezone("Asia/Kolkata")

def get_stock_data(stock_name: str) -> dict:
    symbol = STOCKS[stock_name]
    ticker = yf.Ticker(symbol)

    hist = ticker.history(period="5d", interval="1h")

    if hist.empty:
        raise ValueError(f"No data for {symbol}")

    latest = hist.iloc[-1]
    prev = hist.iloc[-2]

    current_price = round(float(latest["Close"]), 2)
    prev_price = round(float(prev["Close"]), 2)
    change_pct = round(
        ((current_price - prev_price) / prev_price) * 100, 2
    )

    return {
        "stock": stock_name,
        "symbol": symbol,
        "current_price": current_price,
        "change_pct": change_pct,
        "high_5d": round(float(hist["High"].max()), 2),
        "low_5d": round(float(hist["Low"].min()), 2),
        "avg_volume": round(float(hist["Volume"].mean()), 0),
        "current_volume": round(float(latest["Volume"]), 0),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_intraday_df(stock_name: str) -> pd.DataFrame:
    symbol = STOCKS[stock_name]

    # today's 5-min candles for VWAP
    df = yf.download(
        symbol,
        period="1d",
        interval="5m",
        progress=False
    )

    if df.empty:
        return pd.DataFrame()

    df.columns = [
        col[0] if isinstance(col, tuple) else col
        for col in df.columns
    ]

    # filter to market hours IST
    df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("Asia/Kolkata")
    df = df.between_time("09:15", "15:30")

    return df

def get_all_stocks() -> list:
    results = []
    for stock_name in STOCKS:
        try:
            data = get_stock_data(stock_name)
            print(
                f"{stock_name}: ₹{data['current_price']} "
                f"({data['change_pct']}%)"
            )
            results.append(data)
        except Exception as e:
            print(f"ERROR fetching {stock_name}: {e}")
    return results

if __name__ == "__main__":
    print("Fetching stock data...\n")
    get_all_stocks()

    print("\nFetching intraday candles for VWAP...\n")
    for stock in STOCKS:
        df = get_intraday_df(stock)
        print(f"{stock}: {len(df)} candles today")