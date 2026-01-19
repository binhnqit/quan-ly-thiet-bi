import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN (HÌNH 2)
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
def load_data_v200():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        # BIẾN LƯU NGÀY TIẾP DIỄN (Mặc định ban đầu 2026)
        active_date = pd.to_datetime("2026-01-01") 
        
        for i, row in df_raw.iterrows():
            # Bỏ qua tiêu đề
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- CHẶN DÒNG TRỐNG (TRÁNH TĂNG SỐ ẢO) ---
            if not ma_may or ma_may.lower() in ["nan", ""]:
                continue 

            # --- LOGIC ĐIỀN NGÀY TIẾP DIỄN ---
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse):
                active_date = dt_parse # Cập nhật khi gặp ngày mới
            
            # Chuẩn hóa vùng miền dựa trên Cột F
            v_final = "KHÁC"
            if "BẮC" in vung_raw: v_final = "MIỀN BẮC"
            elif "TRUNG" in vung_raw: v_final = "MIỀN TRUNG"
            elif "NAM" in vung_raw: v_final = "MIỀN NAM"

            final_rows.append({
                "NGÀY_GỐC": ngay_raw if ngay_raw else active_date.strftime('%d/%m/%Y'),
                "DATE_KEY": active_date,
                "THÁNG": active_date.month,
                "NĂM": active_date.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": v_final
            })

        return pd.DataFrame(final_rows)
    except Exception as e:
        st.error(f"Lỗi nạp liệu: {e}")
        return None

# Nạp dữ liệu
data = load_data_v200()

if data is not None:
    # Sidebar lọc
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ 2026")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_m = st.selectbox("Chọn kỳ báo cáo", ["Tất cả năm 2026"] + [f"Tháng {i}" for i in range(1, 13)])

    # Lọc năm 2026
    df_2026 = data[data['NĂM'] == 2026]
    if sel_m == "Tất cả năm 2026":
        df_filtered = df_2026
    else:
        m_num = int(sel_m.replace("Tháng ", ""))
        df_filtered = df_2026[df_2026['THÁNG'] == m_num]

    # --- KPI SECTION (GIỐNG HÌNH 2) ---
    st.markdown(f"## 📊 Báo
