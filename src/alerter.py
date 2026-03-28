import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# add your friend's chat ID here when you have it
CHAT_IDS = [
    os.getenv("TELEGRAM_CHAT_ID"),  # you
    # "friend_chat_id_here",        # your friend — uncomment when ready
]

def send_alert(analysis: dict, chat_id: str):
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
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    })

    if response.status_code == 200:
        print(f"Alert sent to {chat_id} for {analysis['stock']}")
    else:
        print(f"Failed to send to {chat_id}: {response.text}")

def send_all_alerts(analyses: list):
    for chat_id in CHAT_IDS:
        if chat_id:
            for analysis in analyses:
                send_alert(analysis, chat_id)

def send_daily_summary():
    from database import get_todays_summary
    data = get_todays_summary()
    date = data["date"]
    total = data["total_scans"]

    lines = [f"📊 *Daily Summary — {date}*", "━━━━━━━━━━━━━━━"]

    for stock, info in data["stocks"].items():
        lines.append(f"\n*{stock}*")
        lines.append(
            f"  Signals: {info['buy']} BUY · "
            f"{info['sell']} SELL · "
            f"{info['hold']} HOLD"
        )
        if info["best"]:
            b = info["best"]
            lines.append(
                f"  Best: {b['signal']} at "
                f"₹{b['entry']} → ₹{b['target']}"
            )
        else:
            lines.append("  No BUY/SELL signals today")

    lines.append("\n━━━━━━━━━━━━━━━")
    lines.append(f"Total scans today: {total}")

    message = "\n".join(lines)

    for chat_id in CHAT_IDS:
        if chat_id:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, data={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            })
            print(f"Daily summary sent to {chat_id}")

if __name__ == "__main__":
    from data_fetcher import get_all_stocks
    from analyzer import analyze_all
    stocks = get_all_stocks()
    analyses = analyze_all(stocks)
    print("\nSending alerts...\n")
    send_all_alerts(analyses)