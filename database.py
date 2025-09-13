import sqlite3
import pandas as pd
from datetime import date

DB_NAME = "trading_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, asset TEXT, type TEXT, quantity REAL, price REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS portfolio_history (snapshot_date DATE PRIMARY KEY, total_value_usd REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS trading_journal (id INTEGER PRIMARY KEY, transaction_id INTEGER, entry_reason TEXT, exit_reason TEXT, lessons_learned TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (transaction_id) REFERENCES transactions (id))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS watched_wallets (id INTEGER PRIMARY KEY, address TEXT NOT NULL UNIQUE, label TEXT, chain TEXT DEFAULT 'Ethereum')''')
    conn.commit()
    conn.close()


def add_watched_wallet(address, label):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO watched_wallets (address, label) VALUES (?, ?)", (address, label))
    conn.commit()
    conn.close()

def get_watched_wallets():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM watched_wallets ORDER BY label ASC", conn)
    conn.close()
    return df

def remove_watched_wallet(wallet_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watched_wallets WHERE id = ?", (wallet_id,))
    conn.commit()
    conn.close()


def add_transaction(asset, tr_type, quantity, price):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (asset, type, quantity, price) VALUES (?, ?, ?, ?)", (asset, tr_type, quantity, price))
    conn.commit(); conn.close()

def get_all_transactions():
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql_query("SELECT * FROM transactions ORDER BY timestamp DESC", conn); conn.close(); return df

def get_portfolio_summary():
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT asset, SUM(CASE WHEN type = 'BUY' THEN quantity ELSE 0 END) - SUM(CASE WHEN type = 'SELL' THEN quantity ELSE 0 END) as total_quantity FROM transactions WHERE type IN ('BUY', 'SELL') GROUP BY asset HAVING total_quantity > 0;"
    df = pd.read_sql_query(query, conn); conn.close(); return df

def get_total_deposits():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute("SELECT SUM(quantity) FROM transactions WHERE type = 'DEPOSIT'"); total = cursor.fetchone()[0]; conn.close(); return total if total else 0.0

def add_portfolio_snapshot(value):
    today = date.today(); conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO portfolio_history (snapshot_date, total_value_usd) VALUES (?, ?)", (today, value))
    conn.commit(); conn.close()

def get_portfolio_history():
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql_query("SELECT * FROM portfolio_history ORDER BY snapshot_date ASC", conn); conn.close()
    if not df.empty:
        df['snapshot_date'] = pd.to_datetime(df['snapshot_date']); df = df.set_index('snapshot_date')
    return df

def add_journal_entry(transaction_id, entry_reason, exit_reason, lessons_learned):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute("INSERT INTO trading_journal (transaction_id, entry_reason, exit_reason, lessons_learned) VALUES (?, ?, ?, ?)", (transaction_id, entry_reason, exit_reason, lessons_learned))
    conn.commit(); conn.close()

def get_journal_entries():
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT j.id, j.timestamp, t.asset, t.type, t.quantity, t.price, j.entry_reason, j.exit_reason, j.lessons_learned FROM trading_journal j JOIN transactions t ON j.transaction_id = t.id ORDER BY j.timestamp DESC"
    df = pd.read_sql_query(query, conn); conn.close(); return df