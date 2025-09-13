# File: database.py (Versi Final dengan Turso & libsql-client)

import os
import pandas as pd
from datetime import date
import libsql_client # <-- Menggunakan library baru
from dotenv import load_dotenv

load_dotenv()

# Fungsi untuk membuat koneksi ke Turso
def create_connection():
    url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    if not url:
        raise ValueError("URL Database Turso tidak ditemukan di environment variables.")
    # Untuk koneksi lokal saat testing, auth_token bisa dikosongkan
    return libsql_client.create_client(url=url, auth_token=auth_token)

def init_db():
    with create_connection() as conn:
        conn.batch([
            "CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, asset TEXT, type TEXT, quantity REAL, price REAL)",
            "CREATE TABLE IF NOT EXISTS portfolio_history (snapshot_date DATE PRIMARY KEY, total_value_usd REAL)",
            "CREATE TABLE IF NOT EXISTS trading_journal (id INTEGER PRIMARY KEY, transaction_id INTEGER, entry_reason TEXT, exit_reason TEXT, lessons_learned TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (transaction_id) REFERENCES transactions (id))",
            "CREATE TABLE IF NOT EXISTS watched_wallets (id INTEGER PRIMARY KEY, address TEXT NOT NULL UNIQUE, label TEXT, chain TEXT DEFAULT 'Ethereum')"
        ])

def add_transaction(asset, tr_type, quantity, price):
    with create_connection() as conn:
        conn.execute(
            "INSERT INTO transactions (asset, type, quantity, price) VALUES (?, ?, ?, ?)",
            (asset, tr_type, quantity, price)
        )

def get_all_transactions():
    with create_connection() as conn:
        rs = conn.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        return pd.DataFrame(rs.rows, columns=rs.columns)

def get_portfolio_summary():
    with create_connection() as conn:
        query = "SELECT asset, SUM(CASE WHEN type = 'BUY' THEN quantity ELSE 0 END) - SUM(CASE WHEN type = 'SELL' THEN quantity ELSE 0 END) as total_quantity FROM transactions WHERE type IN ('BUY', 'SELL') GROUP BY asset HAVING total_quantity > 0;"
        rs = conn.execute(query)
        return pd.DataFrame(rs.rows, columns=rs.columns)

def get_total_deposits():
    with create_connection() as conn:
        rs = conn.execute("SELECT SUM(quantity) FROM transactions WHERE type = 'DEPOSIT'")
        return rs.rows[0][0] if rs.rows else 0.0

def add_portfolio_snapshot(value):
    today = date.today().isoformat()
    with create_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO portfolio_history (snapshot_date, total_value_usd) VALUES (?, ?)",
            (today, value)
        )

def get_portfolio_history():
    with create_connection() as conn:
        rs = conn.execute("SELECT * FROM portfolio_history ORDER BY snapshot_date ASC")
        df = pd.DataFrame(rs.rows, columns=rs.columns)
        if not df.empty:
            df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
            df = df.set_index('snapshot_date')
        return df

def add_journal_entry(transaction_id, entry_reason, exit_reason, lessons_learned):
    with create_connection() as conn:
        conn.execute(
            "INSERT INTO trading_journal (transaction_id, entry_reason, exit_reason, lessons_learned) VALUES (?, ?, ?, ?)",
            (transaction_id, entry_reason, exit_reason, lessons_learned)
        )

def get_journal_entries():
    with create_connection() as conn:
        query = "SELECT j.id, j.timestamp, t.asset, t.type, t.quantity, t.price, j.entry_reason, j.exit_reason, j.lessons_learned FROM trading_journal j JOIN transactions t ON j.transaction_id = t.id ORDER BY j.timestamp DESC"
        rs = conn.execute(query)
        return pd.DataFrame(rs.rows, columns=rs.columns)

def add_watched_wallet(address, label):
    with create_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO watched_wallets (address, label) VALUES (?, ?)", (address, label))

def get_watched_wallets():
    with create_connection() as conn:
        rs = conn.execute("SELECT * FROM watched_wallets ORDER BY label ASC")
        return pd.DataFrame(rs.rows, columns=rs.columns)

def remove_watched_wallet(wallet_id):
    with create_connection() as conn:
        conn.execute("DELETE FROM watched_wallets WHERE id = ?", (wallet_id,))