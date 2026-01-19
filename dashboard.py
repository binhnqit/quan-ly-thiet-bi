import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống AI 3651 - V52", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v52():
    try:
        # Thêm cache buster để lấy đúng 3.651 dòng
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, header=None, on_bad_lines='skip', dtype=str).fillna("")
        
        # QUÉT DÒNG TIÊU ĐỀ THÔNG MINH (Tránh lỗi Merge Cell dòng 1)
        header_idx = 0
        found = False
        for i in range(min(15, len(df_raw))):
            line_str = " ".join([str(x) for x in df_raw.iloc[i]]).upper()
            if any(k in line_str for k in ['MÃ', 'NGÀY', 'LÝ DO']):
                header_idx = i
                found = True
                break
        
        if not found:
            return None

        # Thiết lập Tiêu đề cột
        headers = [str(c).strip().upper() for c in df_raw.iloc[header_idx]]
        df = df_raw.iloc[header_idx+1:].copy()
        df.columns = headers
        
        # Tìm các cột quan trọng
        def find_col(keywords):
            for k in keywords:
                for name in headers:
                    if k in str(name): return name
            return None

        c_ma = find_col(['MÃ', 'MA', 'ID'])
        c_ly = find_col(['LÝ DO', 'NỘI DUNG', 'CHI TIẾT', 'LOI'])
        c_ng = find_col(['NGÀY', 'NGAY', 'DATE'])

        if not c_ma or not c_ng:
            return None

        # Xử lý dữ liệu sạch
        new_df = pd.DataFrame()
        new_df['MÃ_MÁY'] = df[c_ma].astype(str).str.split('.').str[0].str.strip()
        new_df['LÝ_DO'] = df[c_ly].astype(str).str.strip()
        new_df['NGÀY_GỐC'] = pd.to_datetime(df[c_ng], dayfirst=True, errors='coerce')
        
        # Chỉ lấy các dòng có mã máy
        new_df = new_df[new_df['MÃ_MÁY'] != ""].copy()
        
        # Tạo cột Năm/Tháng
        new_df['NĂM'] = new_df['NGÀY_GỐC'].dt.year.fillna(0).astype(int)
        new_df['THÁNG_SO'] = new_df['NGÀY_GỐC'].dt.month.fillna(0).astype(int)
        
        return new_df
    except Exception:
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🚀 CẬP NHẬT 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v52()
    
    if data is not None:
        st.success(f"✅ Đã nhận {len(data)} dòng")
        # Lọc Năm
        years = sorted([y for y in data['NĂM'].unique() if y > 0], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + years)
        
        # Lọc Tháng
        sel_month = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])
        
        df_filtered = data.copy()
        if sel_year != "Tất cả":
            df_final_data = df_filtered[df_
