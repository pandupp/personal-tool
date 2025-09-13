import streamlit as st
import nest_asyncio
nest_asyncio.apply() 
import pandas as pd
import yfinance as yf
from database import init_db, add_transaction, get_all_transactions, get_portfolio_summary, get_total_deposits, add_portfolio_snapshot, get_portfolio_history, add_journal_entry, get_journal_entries, add_watched_wallet, get_watched_wallets, remove_watched_wallet
from ai_module import dapatkan_analisis_ai
from market_data import get_fear_and_greed_index, get_btc_dominance, get_usd_to_idr_rate
from whale_watcher import get_latest_transactions

# --- FUNGSI-FUNGSI ---
def local_css(file_name):
    with open(file_name) as f: st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def diagnose_market_regime(war_mode, ticker="BTC-USD"):
    try:
        data = yf.Ticker(ticker).history(period="250d"); sma_200 = data['Close'].rolling(window=200).mean().iloc[-1]; current_price = data['Close'].iloc[-1]
        if current_price > sma_200:
            reason = f"Pasukan utama (${current_price:,.2f}) memimpin di depan garis logistik (${sma_200:,.2f})." if war_mode else f"Harga BTC (${current_price:,.2f}) di atas SMA 200 (${sma_200:,.2f})."
            regime = "Cerah (Risk-On)" if war_mode else "Bullish (Risk-On)"
            return regime, reason
        else:
            reason = f"Pasukan utama (${current_price:,.2f}) tertinggal dari garis logistik (${sma_200:,.2f})." if war_mode else f"Harga BTC (${current_price:,.2f}) di bawah SMA 200 (${sma_200:,.2f})."
            regime = "Badai (Risk-Off)" if war_mode else "Bearish (Risk-Off)"
            return regime, reason
    except: return "Error", "Gagal menganalisis."

def calculate_momentum_allocation(assets, days=30):
    tickers = [f"{a}-USD" for a in assets]; data = yf.download(tickers, period=f"{days+1}d")['Close']
    if data.empty: return None
    returns = data.pct_change(days).iloc[-1].clip(lower=0)
    if returns.sum() == 0: return {a: 1/len(assets) for a in assets}
    weights = returns / returns.sum(); return {k.replace('-USD', ''): v for k, v in weights.to_dict().items()}

def calculate_risk_based_allocation(assets, days=30):
    tickers = [f"{a}-USD" for a in assets]; data = yf.download(tickers, period=f"{days}d")['Close']
    if data.empty: return None
    returns = data.pct_change().dropna(); volatility = returns.std(); inv_vol = 1 / volatility
    weights = inv_vol / inv_vol.sum(); return {k.replace('-USD', ''): v for k, v in weights.to_dict().items()}

# --- FUNGSI HALAMAN ---
def display_dashboard(war_mode, currency_symbol, currency_format, currency_rate):
    TEXT_MAP = { "title": "Pusat Komando Digital" if war_mode else "Pandu Terminal", "subtitle": "*Perang Informasi di Medan Perang Finansial.*" if war_mode else "*Clarity in Chaos.*", "market_health_header": "📡 Laporan Intelijen Medan Perang" if war_mode else "🩺 Status Kesehatan Pasar", "fng_label": "Moral Pasukan Musuh" if war_mode else "Fear & Greed Index", "dom_label": "Kontrol Teritori Utama" if war_mode else "BTC Dominance", "regime_label": "Kondisi Cuaca Perang" if war_mode else "Musim Pasar (Regime)", "portfolio_header": "🎖️ Status Kekuatan Militer" if war_mode else "📈 Ringkasan Portofolio", "portfolio_value": "Total Kekuatan Tempur" if war_mode else "Nilai Portofolio", "capital_value": "Total Sumber Daya" if war_mode else "Modal Investasi", "pl_value": "Wilayah Dikuasai/Hilang" if war_mode else "Profit/Loss", "asset_details": "Rincian Unit Pasukan" if war_mode else "Rincian Aset", "asset_col": "Unit Pasukan" if war_mode else "Aset", "qty_col": "Kekuatan" if war_mode else "Jumlah", "value_col": f"Nilai ({currency_symbol})", "alloc_col": "Dispersi Pasukan" if war_mode else "Alokasi", "growth_chart": "Grafik Kekuatan Tempur" if war_mode else "Grafik Pertumbuhan Portofolio", "allocation_module": "🗺️ Meja Perencanaan Strategis" if war_mode else "🧠 Modul Alokasi Aset Strategis", "new_funds": f"Jumlah Amunisi Baru ({currency_symbol}):" if war_mode else f"Dana tambahan ({currency_symbol}):", "strategy_select": "Pilih Doktrin Perang:" if war_mode else "Pilih Strategi Alokasi:", "strat_expert": "🎖️ Sang Jenderal AI" if war_mode else "🤖 Alokasi Cerdas Otomatis", "strat_shield": "🛡️ Formasi Bertahan" if war_mode else "🛡️ Berbasis Risiko", "strat_prop": "📊 Pergerakan Serentak" if war_mode else "📈 Proporsional", "strat_custom": "✍️ Rencana Sendiri" if war_mode else "✍️ Kustom", "reco_button": "Gelar Rencana Perang" if war_mode else "Hitung Rekomendasi", "reco_header": "✅ Perintah Operasi" if war_mode else "✅ Hasil Rekomendasi", "ai_header": "🤖 Penasihat AI Jenderal" if war_mode else "🤖 Asisten Riset AI", "ai_topic": "Minta analisis intelijen tentang:" if war_mode else "Topik riset:", "ai_button": "Mulai Analisis" if war_mode else "Hasilkan Analisis", "tx_expander": "Logistik & Arsip Pertempuran" if war_mode else "Catat Transaksi / Lihat Riwayat", "tx_form": "Catat Manuver Pasukan" if war_mode else "Catat Transaksi Baru", "tx_history": "Arsip Pertempuran" if war_mode else "Riwayat Transaksi",}
    st.title(TEXT_MAP["title"]); st.write(TEXT_MAP["subtitle"])
    st.markdown("---"); st.header(TEXT_MAP["market_health_header"])
    fng, btc_dom, (regime, reason) = get_fear_and_greed_index(), get_btc_dominance(), diagnose_market_regime(war_mode)
    c1,c2,c3=st.columns(3); c1.metric(TEXT_MAP["fng_label"], fng); c2.metric(TEXT_MAP["dom_label"], btc_dom); c3.metric(TEXT_MAP["regime_label"], regime, help=reason)
    st.markdown("---"); st.header(TEXT_MAP["portfolio_header"])
    portfolio_df, total_deposits_usd, total_portfolio_value_usd, asset_values = get_portfolio_summary(), get_total_deposits(), 0.0, {}
    if not portfolio_df.empty:
        assets, tickers = portfolio_df['asset'].tolist(), [f"{a}-USD" for a in portfolio_df['asset'].tolist()]
        try:
            live_prices = yf.Tickers(tickers)
            for _, row in portfolio_df.iterrows():
                asset, quantity = row['asset'], row['total_quantity']
                price = live_prices.tickers[f'{asset}-USD'].history(period='1d')['Close'].iloc[-1]
                asset_values[asset] = {'quantity': quantity, 'value_usd': quantity * price}; total_portfolio_value_usd += asset_values[asset]['value_usd']
        except Exception as e:
            st.error(f"Gagal mengambil data harga saat ini. Error: {e}")
    if st.session_state.price_alert:
        alert = st.session_state.price_alert; alert_price_display = alert['price'] * currency_rate
        currency_format_alert = "Rp {:,.0f}" if currency_rate > 1 else "${:,.2f}"
        st.sidebar.info(f"Aktif: {alert['asset']} {alert['condition']} {currency_format_alert.format(alert_price_display)}")
        try:
            live_price_usd = yf.Ticker(f"{alert['asset']}-USD").history(period='1d')['Close'].iloc[-1]
            if (alert['condition'] == '>' and live_price_usd > alert['price']) or (alert['condition'] == '<' and live_price_usd < alert['price']):
                st.toast(f"🔔 ALERT: {alert['asset']} {alert['condition']} {currency_format_alert.format(alert['price']*currency_rate)}!", icon='💰'); st.session_state.price_alert = None
        except: st.sidebar.warning(f"Gagal cek harga {alert['asset']}.")
    if total_portfolio_value_usd > 0: add_portfolio_snapshot(total_portfolio_value_usd)
    total_pl_usd, pl_percent = total_portfolio_value_usd - total_deposits_usd, (total_portfolio_value_usd - total_deposits_usd) / total_deposits_usd * 100 if total_deposits_usd > 0 else 0
    c1, c2, c3 = st.columns(3); c1.metric(TEXT_MAP["portfolio_value"], currency_format.format(total_portfolio_value_usd * currency_rate)); c2.metric(TEXT_MAP["capital_value"], currency_format.format(total_deposits_usd * currency_rate)); c3.metric(TEXT_MAP["pl_value"], currency_format.format(total_pl_usd * currency_rate), f"{pl_percent:.2f}%")
    asset_df_display = pd.DataFrame([{'Aset': k, 'Jumlah': v['quantity'], 'Nilai': v['value_usd'] * currency_rate} for k,v in asset_values.items()])
    if not asset_df_display.empty:
        asset_df_display.columns = [TEXT_MAP['asset_col'], TEXT_MAP['qty_col'], TEXT_MAP['value_col']]
        asset_df_display[TEXT_MAP['alloc_col']] = (asset_df_display[TEXT_MAP['value_col']] / (total_portfolio_value_usd * currency_rate) * 100) if total_portfolio_value_usd > 0 else 0
        st.subheader(TEXT_MAP["asset_details"]); st.dataframe(asset_df_display.style.format({TEXT_MAP['value_col']: currency_format, TEXT_MAP['alloc_col']: '{:.2f}%'}), width='stretch')
    st.subheader(TEXT_MAP["growth_chart"]); history_df = get_portfolio_history()
    if history_df.empty: st.info("Buka aplikasi setiap hari untuk membangun grafik.")
    else: st.line_chart(history_df['total_value_usd'] * currency_rate)
    st.markdown("---"); st.header(TEXT_MAP["allocation_module"])
    new_funds = st.number_input(TEXT_MAP["new_funds"], 0.0, step=100.0, format="%.2f")
    strategy_options = [TEXT_MAP["strat_expert"], TEXT_MAP["strat_shield"], TEXT_MAP["strat_prop"], TEXT_MAP["strat_custom"]]
    strategy = st.selectbox(TEXT_MAP["strategy_select"], strategy_options)
    if strategy == TEXT_MAP["strat_custom"]:
        st.subheader("Definisikan Alokasi Kustom (%)"); assets_custom = ["BTC", "ETH", "SOL", "USDT", "Lainnya"]; cols = st.columns(len(assets_custom));
        custom_allocations = {asset: c.number_input(f"% {asset}", 0, 100, 0, 5, key=f"c_{asset}") for asset, c in zip(assets_custom, cols)}; total_percent = sum(custom_allocations.values())
        if total_percent != 100: st.warning(f"Total alokasi {total_percent}%. Pastikan 100%.")
    if st.button(TEXT_MAP["reco_button"]):
        if new_funds > 0:
            recos, assets_to_analyze = [], ['BTC', 'ETH', 'SOL']; weights = None; new_funds_usd = new_funds / currency_rate
            if strategy == TEXT_MAP["strat_expert"]:
                with st.spinner("Mendiagnosis medan perang..."):
                    regime, reason = diagnose_market_regime(war_mode); st.info(f"**Status Medan Perang: {regime}**\n\n*{reason}*")
                    if "Cerah" in regime or "Bullish" in regime: st.write("✅ **Doktrin Aktif: Serangan Cepat (Momentum)**"); weights = calculate_momentum_allocation(assets_to_analyze)
                    else: st.write("🛡️ **Doktrin Aktif: Formasi Bertahan (Risiko)**"); weights = calculate_risk_based_allocation(assets_to_analyze)
            elif strategy == TEXT_MAP["strat_shield"]:
                with st.spinner("Menganalisis volatilitas..."): weights = calculate_risk_based_allocation(assets_to_analyze)
            elif strategy == TEXT_MAP["strat_prop"]:
                if not asset_df_display.empty: weights = {row[TEXT_MAP['asset_col']]: row[TEXT_MAP['alloc_col']]/100 for _, row in asset_df_display.iterrows()}
            elif strategy == TEXT_MAP["strat_custom"]:
                if total_percent == 100: weights = {k: v/100 for k, v in custom_allocations.items() if v > 0}
                else: st.error("Total persentase kustom harus 100%.")
            if weights:
                for asset, weight in weights.items(): recos.append({"Aset": asset, "Alokasi": (new_funds_usd * weight) * currency_rate, "Bobot": f"{weight:.2%}"})
                reco_df = pd.DataFrame(recos); reco_df.columns = [TEXT_MAP["asset_col"], f"Alokasi Amunisi ({currency_symbol})", "Bobot"]
                st.subheader(TEXT_MAP["reco_header"]); st.dataframe(reco_df.style.format({f"Alokasi Amunisi ({currency_symbol})": currency_format}), width='stretch')
        else: st.warning("Masukkan jumlah amunisi.")
    st.markdown("---"); st.header(TEXT_MAP["ai_header"])
    ai_topic = st.text_input(TEXT_MAP["ai_topic"], "Prospek Bitcoin (BTC) minggu depan")
    if st.button(TEXT_MAP["ai_button"]):
        if ai_topic:
            with st.spinner("Memanggil intelijen..."): st.markdown(dapatkan_analisis_ai(ai_topic))
        else: st.warning("Masukkan topik intelijen.")
    st.markdown("---")
    with st.expander(TEXT_MAP["tx_expander"]):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(TEXT_MAP["tx_form"]); asset = st.selectbox("Unit", ["BTC", "ETH", "USDT", "SOL", "BNB"], key="asset_input"); tr_type = st.selectbox("Manuver", ["BUY", "SELL", "DEPOSIT"], key="type_input")
            quantity = st.number_input("Kekuatan", 0.0, format="%.6f", key="q_input"); price_input = st.number_input(f"Harga per Unit ({currency_symbol})", 0.0, format="%.2f", key="p_input")
            if st.button("Simpan Laporan"):
                if quantity > 0: price_in_usd = price_input / currency_rate; add_transaction(asset, tr_type, quantity, price_in_usd); st.success("Laporan tersimpan!"); st.rerun()
                else: st.warning("Kekuatan harus > 0.")
        with c2:
            st.subheader(TEXT_MAP["tx_history"]); all_data = get_all_transactions()
            if all_data.empty: st.info("Arsip kosong.")
            else: st.dataframe(all_data, width='stretch')

def display_journal(war_mode, currency_format, currency_rate):
    st.title("📜 Laporan Pasca-Pertempuran (AAR)" if war_mode else "📓 Jurnal Trading")
    st.write("Refleksikan manuver tempur." if war_mode else "Refleksikan keputusan trading Anda.")
    st.subheader("✍️ Tambah Laporan Baru" if war_mode else "✍️ Tambah Entri Jurnal Baru")
    all_transactions = get_all_transactions()
    if not all_transactions.empty:
        all_transactions['display'] = all_transactions.apply(lambda r: f"ID: {r['id']} | {r['timestamp'][5:16]} | {r['type']} {r['asset']}", axis=1)
        selected_trx = st.selectbox("Pilih Manuver:" if war_mode else "Pilih Transaksi:", all_transactions['display'])
        trx_id = int(selected_trx.split(" | ")[0].split(": ")[1])
        entry_reason = st.text_area("Alasan membuka pertempuran?" if war_mode else "Alasan masuk posisi?")
        exit_reason = st.text_area("Rencana/Alasan mundur?" if war_mode else "Rencana/Alasan keluar?")
        lessons_learned = st.text_area("Pelajaran dari pertempuran ini?" if war_mode else "Pelajaran yang didapat?")
        if st.button("Simpan Laporan" if war_mode else "Simpan ke Jurnal"):
            if trx_id and entry_reason and lessons_learned: add_journal_entry(trx_id, entry_reason, exit_reason, lessons_learned); st.success("Laporan tersimpan!"); st.rerun()
            else: st.warning("Isi semua kolom.")
    else: st.info("Lakukan manuver terlebih dahulu.")
    st.markdown("---")
    st.subheader("📚 Arsip Laporan" if war_mode else "📚 Riwayat Jurnal")
    journal_entries = get_journal_entries()
    if journal_entries.empty: st.info("Belum ada laporan.")
    else:
        for _, row in journal_entries.iterrows():
            with st.expander(f"**Laporan untuk {row['type']} {row['asset']}** ({pd.to_datetime(row['timestamp']).strftime('%d %b %Y')})"):
                price_display = (row['price'] * currency_rate) if row['price'] else 0
                st.markdown(f"**Detail Manuver:** {row['quantity']} {row['asset']} @ {currency_format.format(price_display)}")
                st.markdown(f"**Alasan Tempur:**\n{row['entry_reason']}\n\n**Strategi Mundur:**\n{row['exit_reason']}\n\n**Pelajaran:**\n{row['lessons_learned']}")

def display_whale_watcher(war_mode):
    st.title("👁️ Unit Mata-Mata" if war_mode else "🐳 Whale Watcher")
    st.write("Pantau pergerakan Jenderal lain." if war_mode else "Pantau pergerakan wallet penting.")
    with st.expander("Kelola Daftar Pantau"):
        c1, c2 = st.columns(2); new_address = c1.text_input("Alamat:", placeholder="0x..."); new_label = c2.text_input("Label:", placeholder="Vitalik Buterin")
        if st.button("Tambah ke Daftar Pantau"):
            if new_address and new_label: add_watched_wallet(new_address, new_label); st.success(f"'{new_label}' ditambahkan!"); st.rerun()
            else: st.warning("Alamat dan Label kosong.")
        st.subheader("Daftar Pantau")
        watchlist = get_watched_wallets()
        if watchlist.empty: st.info("Daftar pantau kosong.")
        else:
            for _, row in watchlist.iterrows():
                c1, c2 = st.columns([0.8, 0.2]); c1.write(f"**{row['label']}**: `{row['address']}`")
                if c2.button("Hapus", key=f"del_{row['id']}"): remove_watched_wallet(row['id']); st.rerun()
    st.markdown("---")
    if not watchlist.empty:
        watchlist_dict = pd.Series(watchlist.address.values, index=watchlist.label).to_dict()
        selected_label = st.selectbox("Pilih Target Intelijen:" if war_mode else "Pilih Wallet untuk Dilacak:", list(watchlist_dict.keys()))
        if selected_label:
            addr = watchlist_dict[selected_label]
            with st.spinner(f"Mengambil data intelijen untuk {selected_label}..."):
                txs = get_latest_transactions(addr)
                if isinstance(txs, pd.DataFrame):
                    if txs.empty: st.info(f"Tidak ada transaksi token terbaru untuk '{selected_label}'.")
                    else: st.dataframe(txs, width='stretch')
                else: st.error(txs)

# --- STRUKTUR UTAMA APLIKASI ---
init_db()
st.set_page_config(layout="wide", page_title="Pandu Terminal")
local_css("style.css")
if 'price_alert' not in st.session_state: st.session_state.price_alert = None

st.sidebar.title("Pengaturan")
war_mode = st.sidebar.toggle("Aktifkan Mode Ruang Perang 🛡️", help="Ubah semua istilah finansial menjadi metafora perang.")
idr_mode = st.sidebar.toggle("Tampilkan dalam Rupiah (IDR) 🇮🇩", help="Konversi semua nilai ke Rupiah.")
if idr_mode:
    currency_symbol, usd_to_idr_rate, currency_format = "Rp", get_usd_to_idr_rate(), "Rp {:,.0f}"
else:
    currency_symbol, usd_to_idr_rate, currency_format = "$", 1.0, "${:,.2f}"
page_options = ["📈 Dashboard", "📓 Jurnal", "🐳 Whale Watcher"]
if war_mode: page_options = ["🎖️ Pusat Komando", "📜 Laporan (AAR)", "👁️ Intelijen"]
page = st.sidebar.radio("Navigasi", page_options)
st.sidebar.markdown("---")

if page in ["📈 Dashboard", "🎖️ Pusat Komando"]:
    with st.sidebar:
        alert_header = "🔔 Peringatan Garis Depan" if war_mode else "🔔 Notifikasi Harga"
        st.header(alert_header); assets_list = ["BTC", "ETH", "SOL", "BNB"]
        alert_asset = st.selectbox("Unit Pasukan:" if war_mode else "Aset:", assets_list); alert_condition = st.selectbox("Kondisi:", ["Tembus ke Atas >" if war_mode else "Di Atas >", "Jatuh ke Bawah <" if war_mode else "Di Bawah <"])
        alert_price_input = st.number_input("Level Koordinat Peta:" if war_mode else f"Level Harga ({currency_symbol}):", 0.0, format="%.2f")
        if st.button("Atur Peringatan" if war_mode else "Atur Notifikasi"):
            price_in_usd = alert_price_input / usd_to_idr_rate
            condition_symbol = ">" if ">" in alert_condition else "<"; st.session_state.price_alert = {"asset": alert_asset, "condition": condition_symbol, "price": price_in_usd}; st.success("Peringatan diatur.")
    display_dashboard(war_mode, currency_symbol, currency_format, usd_to_idr_rate)
elif page in ["📓 Jurnal", "📜 Laporan (AAR)"]:
    display_journal(war_mode, currency_format, usd_to_idr_rate)
else:
    display_whale_watcher(war_mode)