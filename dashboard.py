import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. GIAO DIỆN CHUẨN (HÌNH 2)
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi 2026", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    div[data-testid="stMetric"] {
        background-color: white; border-radius: 10px; padding: 15px;
        border-left: 5px solid #1E3A8A; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v195():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        # BIẾN LƯU NGÀY HIỆN TẠI (Quan trọng: Mặc định ban đầu là ngày đầu năm 2026)
        active_date = pd.to_datetime("01/01/2026", dayfirst=True) 
        
        for i, row in df_raw.iterrows():
            # Bỏ qua dòng tiêu đề và các dòng không có mã máy (Cột B - Index 1)
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_f = str(row.iloc[5]).strip().upper()

            # --- CHẶN DÒNG TRỐNG: Nếu không có Mã máy thì không đếm (Tránh số ảo) ---
            if not ma_may or ma_may.lower() in ["nan", ""]:
                continue 

            # --- LOGIC ĐIỀN NGÀY TIẾP DIỄN ---
            # Thử đọc ngày từ cột A
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            
            # Nếu dòng này có ghi ngày mới -> Cập nhật ngày đang lưu
            if pd.notnull(dt_parse):
                active_date = dt_parse
            
            # Dòng này dù trống ngày nhưng có mã máy -> Sẽ lấy ngày 'active_date' đang nhớ
            final_rows.append({
                "NGÀY_GỐC": ngay_raw if ngay_raw else active_date.strftime('%d/%m/%Y'),
                "DATE_KEY": active_date,
                "THÁNG": active_date.month,
                "NĂM": active_date.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": vung_f
            })

        df = pd.DataFrame(final_rows)
        # Chuẩn hóa Vùng Miền để biểu đồ Donut khớp Hình 2
        df['VÙNG_CHỈNH'] = df['VÙNG'].apply(lambda x: "MIỀN BẮ
