import schedule
import time
from datetime import datetime
import pytz

from data_fetcher import get_all_stocks
from analyzer import analyze_all
from alerter import send_all_alerts

IST = pytz.timezone("Asia/Kolkata")

def is_market_open() -> bool:
    now = datetime.now(IST)
    # market open Mon-Fri, 9:15am - 3:30pm IST
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    market_open = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    return market_open <= now <= market_close

def run_scan():
    now = datetime.now(IST).strftime("%H:%M:%S")
    print(f"\n[{now}] Running scan...")

    if not is_market_open():
        print("Market is closed. Skipping scan.")
        return

    try:
        stocks = get_all_stocks()
        analyses = analyze_all(stocks)
        send_all_alerts(analyses)
        print("Scan complete.")
    except Exception as e:
        print(f"ERROR during scan: {e}")

if __name__ == "__main__":
    print("Stock Assistant started!")
    print("Scanning every 1 minute during market hours (9:15am - 3:30pm IST)")
    print("Press Ctrl+C to stop\n")

    # run once immediately
    run_scan()

    # then every 1 minute
    schedule.every(1).minutes.do(run_scan)

    while True:
        schedule.run_pending()
        time.sleep(1)