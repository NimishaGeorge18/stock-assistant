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

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully")