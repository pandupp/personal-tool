import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

def get_latest_transactions(wallet_address, limit=25):
    """Mengambil transaksi token ERC-20 terakhir dari sebuah alamat wallet."""
    if not ETHERSCAN_API_KEY:
        return "Error: Kunci API Etherscan tidak ditemukan di file .env"

    api_url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&page=1&offset={limit}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        if data['status'] == '1' and data['result']:
            df = pd.DataFrame(data['result'])
            
            
            df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0)
            df['tokenDecimal'] = pd.to_numeric(df['tokenDecimal'], errors='coerce').fillna(18).astype(int)

            
            df['value'] = df.apply(
                lambda row: row['value'] / (10**row['tokenDecimal']) if row['tokenDecimal'] > 0 else row['value'],
                axis=1
            )
            
            df['timeStamp'] = pd.to_datetime(df['timeStamp'], unit='s')
            df['Arah'] = df.apply(lambda row: 'KELUAR' if row['from'].lower() == wallet_address.lower() else 'MASUK', axis=1)
            
            df_clean = df[['timeStamp', 'Arah', 'tokenSymbol', 'value', 'to', 'from']]
            df_clean.columns = ['Waktu', 'Arah', 'Aset', 'Jumlah', 'Ke', 'Dari']
            return df_clean
        else:
            return pd.DataFrame() 
    except Exception as e:
        return f"Error saat menghubungi Etherscan: {e}"