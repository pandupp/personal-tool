
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    
    try:
        import streamlit as st
        st.error("GOOGLE_API_KEY tidak ditemukan. Pastikan file .env Anda sudah benar.")
    except ImportError:
        raise ValueError("GOOGLE_API_KEY tidak ditemukan. Pastikan file .env Anda sudah benar.")

genai.configure(api_key=api_key)

def dapatkan_analisis_ai(topik_analisis: str) -> str:
    """
    Mengirim prompt ke model AI Gemini dan mengembalikan responsnya sebagai teks.
    """
    
    current_date = datetime.now().strftime('%d %B %Y')

    prompt_final = f"""
    Peran: Anda adalah seorang analis pasar kripto senior yang memberikan briefing pagi kepada seorang trader.
    Gaya Bahasa: Langsung ke intinya, padat, berbasis data, dan percaya diri.
    
    Konteks Waktu: Anggap saat ini adalah tanggal **{current_date}**. Gunakan informasi terbaru yang Anda miliki untuk analisis ini. Fokus pada peristiwa dan data dari beberapa bulan terakhir jika memungkinkan.

    Tugas: Berikan briefing strategis untuk topik berikut: '{topik_analisis}'.

    Struktur Jawaban yang WAJIB Anda ikuti:
    
    ### [Nama Aset] Outlook - {current_date}
    
    * **Kesimpulan & Sentimen:** (1 Kalimat. Tentukan apakah sentimennya Bullish, Bearish, atau Netral untuk jangka pendek dan berikan alasan utamanya).
    
    * **Analisis Kunci:**
        * **Teknikal:** Sebutkan level support & resistance kunci yang **spesifik** dan relevan saat ini. Sebutkan kondisi indikator utama seperti RSI (misal: "RSI di 45, menunjukkan kondisi netral").
        * **Sentimen & Berita:** Sebutkan 1-2 berita atau narasi **terbaru** yang Anda ketahui yang sedang mempengaruhi pasar.
        * **Faktor Makro/On-Chain:** Pilih satu faktor eksternal (misal: kebijakan The Fed) ATAU satu data on-chain yang paling relevan.
    
    * **Penggerak Pasar Utama Minggu Ini:** (Sebutkan satu peristiwa paling penting yang harus dipantau).
    
    PENTING: Jangan gunakan placeholder. Berikan jawaban seolah-olah Anda memiliki akses ke data pasar terkini.
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_final)
        return response.text
    except Exception as e:
        return f"Terjadi kesalahan saat menghubungi AI: {e}"