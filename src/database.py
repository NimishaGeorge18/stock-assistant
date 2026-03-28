import sqlite3
import os
from datetime import datetime

DB_PATH = "logs/signals.db"
os.makedirs("logs", exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            stock TEXT,
            signal TEXT,
            entry REAL,
            target REAL,
            stop_loss REAL,
            reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_signal(analysis: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO signals 
        (timestamp, stock, signal, entry, target, stop_loss, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        analysis["timestamp"],
        analysis["stock"],
        analysis["signal"],
        analysis["entry"],
        analysis["target"],
        analysis["stop_loss"],
        analysis["reason"]
    ))
    conn.commit()
    conn.close()

def save_all_signals(analyses: list):
    init_db()
    for analysis in analyses:
        save_signal(analysis)
    print(f"Saved {len(analyses)} signals to database")

def get_last_signal(stock: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM signals 
        WHERE stock = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''', (stock,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "timestamp": row[1],
            "stock": row[2],
            "signal": row[3],
            "entry": row[4],
            "target": row[5],
            "stop_loss": row[6],
            "reason": row[7]
        }
    return None

def get_todays_summary() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stocks = ["ITC", "RELIANCE", "ONGC"]
    summary = {}
    total_scans = 0

    for stock in stocks:
        cursor.execute('''
            SELECT signal, entry, target, stop_loss
            FROM signals
            WHERE stock = ? AND timestamp LIKE ?
            ORDER BY timestamp ASC
        ''', (stock, f"{today}%"))

        rows = cursor.fetchall()
        total_scans += len(rows)

        buy_count = sum(1 for r in rows if r[0] == "BUY")
        sell_count = sum(1 for r in rows if r[0] == "SELL")
        hold_count = sum(1 for r in rows if r[0] == "HOLD")

        # find best signal (biggest potential reward)
        best = None
        best_reward = 0
        for row in rows:
            signal, entry, target, sl = row
            if signal in ("BUY", "SELL"):
                reward = abs(target - entry)
                if reward > best_reward:
                    best_reward = reward
                    best = {
                        "signal": signal,
                        "entry": entry,
                        "target": target,
                        "stop_loss": sl
                    }

        summary[stock] = {
            "buy": buy_count,
            "sell": sell_count,
            "hold": hold_count,
            "best": best,
            "total": len(rows)
        }

    conn.close()
    return {"stocks": summary, "total_scans": total_scans, "date": today}

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully")