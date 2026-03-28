import schedule
import time
from datetime import datetime
import pytz

from data_fetcher import get_all_stocks
from analyzer import analyze_all
from alerter import send_all_alerts, send_daily_summary
from database import save_all_signals, init_db

IST = pytz.timezone("Asia/Kolkata")

def is_market_open() -> bool:
    now = datetime.now(IST)
    if now.weekday() >= 5:
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
        save_all_signals(analyses)
        send_all_alerts(analyses)
        print("Scan complete.")
    except Exception as e:
        print(f"ERROR during scan: {e}")

def run_daily_summary():
    now = datetime.now(IST)
    # only send on weekdays
    if now.weekday() < 5:
        print("\nSending daily summary...")
        send_daily_summary()

if __name__ == "__main__":
    init_db()
    print("Stock Assistant started!")
    print("Scanning every 1 minute during market hours")
    print("Daily summary at 3:30 PM IST")
    print("Press Ctrl+C to stop\n")

    run_scan()

    schedule.every(1).minutes.do(run_scan)
    schedule.every().day.at("10:00").do(run_daily_summary)  

    while True:
        schedule.run_pending()
        time.sleep(1)