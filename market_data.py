import requests
import yfinance as yf

def get_fear_and_greed_index():
    try:
        response = requests.get("https://api.alternative.me/fng/?limit=1")
        response.raise_for_status()
        data = response.json()['data'][0]
        return f"{int(data['value'])} ({data['value_classification']})"
    except requests.exceptions.RequestException:
        return "N/A"

def get_btc_dominance():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/global")
        response.raise_for_status()
        dominance = response.json()['data']['market_cap_percentage']['btc']
        return f"{dominance:.2f}%"
    except requests.exceptions.RequestException:
        return "N/A"

# --- FUNGSI BARU UNTUK KURS USD/IDR ---
def get_usd_to_idr_rate():
    """Mengambil kurs USD ke IDR terbaru dari Yahoo Finance."""
    try:
        ticker = yf.Ticker("IDR=X")
        rate = ticker.history(period='1d')['Close'].iloc[-1]
        return rate
    except Exception:
        
        return 16200.0