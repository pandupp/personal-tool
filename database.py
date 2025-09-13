import streamlit as st
import pandas as pd
from datetime import date
from turso_db import Turso

@st.cache_resource
def get_db():
    
    url = st.secrets["TURSO_DATABASE_URL"]
    auth_token = st.secrets["TURSO_AUTH_TOKEN"]
    return Turso(url=url, auth_token=auth_token)

db = get_db()


def init_db():
    
    db.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, asset TEXT, type TEXT, quantity REAL, price REAL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS portfolio_history (snapshot_date DATE PRIMARY KEY, total_value_usd REAL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS trading_journal (id INTEGER PRIMARY KEY, transaction_id INTEGER, entry_reason TEXT, exit_reason TEXT, lessons_learned TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (transaction_id) REFERENCES transactions (id))''')
    db.execute('''CREATE TABLE IF NOT EXISTS watched_wallets (id INTEGER PRIMARY KEY, address TEXT NOT NULL UNIQUE, label TEXT, chain TEXT DEFAULT 'Ethereum')''')


def add_watched_wallet(address, label):
    db.execute("INSERT OR IGNORE INTO watched_wallets (address, label) VALUES (?, ?)", (address, label))

def get_watched_wallets():
    rows = db.execute("SELECT * FROM watched_wallets ORDER BY label ASC")
    df = pd.DataFrame(rows, columns=['id', 'address', 'label', 'chain'])
    return df

def remove_watched_wallet(wallet_id):
    db.execute("DELETE FROM watched_wallets WHERE id = ?", (wallet_id,))


def add_transaction(asset, tr_type, quantity, price):
    db.execute("INSERT INTO transactions (asset, type, quantity, price) VALUES (?, ?, ?, ?)", (asset, tr_type, quantity, price))

def get_all_transactions():
    rows = db.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
    df = pd.DataFrame(rows, columns=['id', 'timestamp', 'asset', 'type', 'quantity', 'price'])
    return df

def get_portfolio_summary():
    query = "SELECT asset, SUM(CASE WHEN type = 'BUY' THEN quantity ELSE 0 END) - SUM(CASE WHEN type = 'SELL' THEN quantity ELSE 0 END) as total_quantity FROM transactions WHERE type IN ('BUY', 'SELL') GROUP BY asset HAVING total_quantity > 0;"
    rows = db.execute(query)
    df = pd.DataFrame(rows, columns=['asset', 'total_quantity'])
    return df

def get_total_deposits():
    result = db.execute("SELECT SUM(quantity) FROM transactions WHERE type = 'DEPOSIT'")[0][0]
    return result if result else 0.0

def add_portfolio_snapshot(value):
    today = date.today()
    db.execute("INSERT OR IGNORE INTO portfolio_history (snapshot_date, total_value_usd) VALUES (?, ?)", (today, value))

def get_portfolio_history():
    rows = db.execute("SELECT * FROM portfolio_history ORDER BY snapshot_date ASC")
    df = pd.DataFrame(rows, columns=['snapshot_date', 'total_value_usd'])
    if not df.empty:
        df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
        df = df.set_index('snapshot_date')
    return df

def add_journal_entry(transaction_id, entry_reason, exit_reason, lessons_learned):
    db.execute("INSERT INTO trading_journal (transaction_id, entry_reason, exit_reason, lessons_learned) VALUES (?, ?, ?, ?)", (transaction_id, entry_reason, exit_reason, lessons_learned))

def get_journal_entries():
    query = "SELECT j.id, j.timestamp, t.asset, t.type, t.quantity, t.price, j.entry_reason, j.exit_reason, j.lessons_learned FROM trading_journal j JOIN transactions t ON j.transaction_id = t.id ORDER BY j.timestamp DESC"
    rows = db.execute(query)
    df = pd.DataFrame(rows, columns=['id', 'timestamp', 'asset', 'type', 'quantity', 'price', 'entry_reason', 'exit_reason', 'lessons_learned'])
    return df