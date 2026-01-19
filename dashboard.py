import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 - V50", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v50():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc toàn bộ file thô dưới dạng String để tránh lỗi định dạng
        df_raw = pd.read_csv(url, header=None, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- CHIẾN THUẬT QUÉT DÒNG TIÊU ĐỀ AN TOÀN ---
        header_idx = 0
        found = False
        
        # Quét 10 dòng đầu tiên để tìm dòng chứa tiêu đề thực sự
        for i in range(min(10, len(df_raw))):
            # Chuyển toàn bộ dòng thành chuỗi để tìm kiếm
            line_str = " ".join([str(x) for x in df_raw.iloc[i]]).upper()
            if 'MÃ' in line_str or 'NGÀY' in line_str or 'ID' in line_str:
                header_idx = i
                found = True
                break
        
        if not found:
            st.error("❌ AI không tìm thấy dòng tiêu đề có chữ 'Mã' hoặc 'Ngày'. Sếp hãy kiểm tra lại dòng 1-5 của file Sheets.")
            return None

        # Thiết lập lại DataFrame từ dòng tìm được
        headers = [str(c).strip().upper() for c in df_raw.iloc[header_idx]]
        df = df_raw.iloc[header_idx+1:].copy()
        df.columns = headers
        
        # Tìm cột thông minh bằng cách quét tên
        def find_col(keywords):
            for k in keywords:
                for idx, name in enumerate(headers):
                    if k in name: return name
            return None

        c_ma = find_col(['MÃ', 'MA', 'ID'])
        c_ly = find_col(['LÝ DO', 'NỘI DUNG', 'CHI TIẾT', 'LOI'])
        c_ng = find_col(['NGÀY', 'NGAY', 'DATE'])

        if not c_ma or not c_ng:
            st.warning(f
