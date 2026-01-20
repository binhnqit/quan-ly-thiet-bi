import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG CHUẨN ELITE ---
st.set_page_config(page_title="LAPTOP MÁY PHA MÀU 4ORANGES", layout="wide", page_icon="🎨")

# CSS TÙY BIẾN MENU & GIAO DIỆN (ĐÃ LÀM SẠCH)
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f0f2f6;
        padding: 10px 10px 0px 10px;
        border-radius: 15px 15px 0px 0px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #ffffff;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        font-weight: bold;
        color: #666;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF8C00 !important;
        color: white !important;
        box-shadow: 0px -4px 10px rgba(255, 140, 0, 0.3);
    }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
        border-left: 5px solid #FF8C00;
    }
</style>
""", unsafe_allow_html=True)

ORANGE_COLORS = ["#FF8C00", "#FFA500", "#FF4500", "#E67E22", "#D35400"]
LOGO_URL = "https://www.4oranges.com/vnt_upload/weblink/Logo_4_Oranges.png"
URL_LAPTOP_LOI = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=675485241&single=true&output=csv"
URL_MIEN_BAC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=602348620&single=true&output=csv"
URL_DA_NANG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=1519063387&single=true&output=csv"

@st.cache_data(ttl=300)
def get_raw_data(url):
    try:
        return pd.read_csv(url, on_bad_lines='skip', low_memory=False).fillna("")
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def process_finance_data(df_loi_raw):
    f_list = []
    if not df_loi_raw.empty:
        for _, row in df_loi_raw.iloc[1:].iterrows():
            try:
                ma = str(row.iloc[1]).strip()
                if not ma or "MÃ" in ma.upper(): continue
                ngay = pd.to_datetime(row.iloc[6], dayfirst=True, errors='coerce')
                if pd.notnull(ngay):
                    cp = pd.to_numeric(str(row.iloc[8]).replace(',', ''), errors='coerce') or 0
                    f_list.append({
                        "NGÀY": ngay, "NĂM": ngay.year, "THÁNG": ngay.month,
                        "MÃ_MÁY": ma, "LINH_KIỆN": str(row.iloc[3]).strip(),
                        "VÙNG": str(row.iloc[5]).strip(), "CP": cp, "KHÁCH": str(row.iloc[2]).strip()
                    })
            except Exception:
                continue
    return pd.DataFrame(f_
