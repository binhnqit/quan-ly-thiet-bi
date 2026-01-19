import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN SANG TRỌNG
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    /* Định dạng thẻ KPI theo phong cách Hình 2 */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v165():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            row_str = " ".join(row.values.astype(str))
            if i == 0 or "Mã số" in row_str: continue
            
            # Lấy dữ liệu chuẩn theo thứ tự cột
            ngay_str = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip().split('.')[0]
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_f = str(row.iloc[5]).strip().upper() # Cột F

            if not ma_may or ma_may == "nan": continue

            # Xử lý thời gian
            dt = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
            thang = dt.month if pd.notnull(dt) else 1
            nam = dt.year if pd.notnull(dt) else 2026

            # Chuẩn hóa nhãn Vùng Miền tuyệt đối từ Cột F
            if "BẮC" in vung_f: v_name = "MIỀN BẮC"
            elif "TRUNG" in vung_f: v_name = "MIỀN TRUNG"
            elif "NAM" in vung_f: v_name = "MIỀN NAM"
            else: v_name = "KHÁC/TRỐNG"

            final_rows.append([ngay_str, dt, thang, nam, ma_may, khach, lk, v_name])

        return pd.DataFrame(final_rows, columns=['NGÀY', 'DT_OBJ', 'THÁNG', 'NĂM', 'MÃ_MÁY', 'KHÁCH_HÀNG
