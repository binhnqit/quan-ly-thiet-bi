import streamlit as st
import pandas as pd
import plotly.express as px
import math
from datetime import datetime

# 1. CẤU HÌNH GIAO DIỆN GỐC
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { 
        background-color: #ffffff; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #1E3A8A;
    }
    .main-title { color: #1E3A8A; font-weight: 800; text-align: center; font-size: 2.2rem; margin-bottom: 20px; }
    .chat-container { background-color: #f0f2f6; padding: 25px; border-radius: 15px; border: 2px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU & CHUẨN HÓA
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(PUBLISHED_URL)
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        def clean_code(val):
            if pd.isna(val): return ""
            return str(val).split('.')[0].strip()
        df['MÃ_MÁY'] = df['COL_1'].apply(clean_code)
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"
        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ").astype(str).str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except: return pd.DataFrame()

df_global = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if not df_global.empty:
        list_years = sorted(df_global['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=list_years.index(2026) if 2026 in list_years else 0)
        list_vung = sorted(df_global['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        df_filtered = df_global[(df_global['NĂM'] == sel_year) & (df_global['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# 3. XỬ LÝ DỮ LIỆU MÁY NGUY
