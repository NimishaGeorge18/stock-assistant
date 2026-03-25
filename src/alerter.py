import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(analysis: dict):
    signal = analysis["signal"]

    if signal == "BUY":
        emoji = "🟢"
    elif signal == "SELL":
        emoji = "🔴"
    else:
        emoji = "🟡"

    message = f"""
{emoji} *{analysis['stock']} — {signal}*
━━━━━━━━━━━━━━━
Entry:      ₹{analysis['entry']}
Target:     ₹{analysis['target']}
Stop Loss:  ₹{analysis['stop_loss']}
━━━━━━━━━━━━━━━
{analysis['reason']}
🕐 {analysis['timestamp']}
""".strip()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })

    if response.status_code == 200:
        print(f"Alert sent for {analysis['stock']}")
    else:
        print(f"Failed to send alert: {response.text}")

def send_all_alerts(analyses: list):
    for analysis in analyses:
        send_alert(analysis)

if __name__ == "__main__":
    from data_fetcher import get_all_stocks
    from analyzer import analyze_all

    stocks = get_all_stocks()
    analyses = analyze_all(stocks)
    print("\nSending alerts...\n")
    send_all_alerts(analyses)