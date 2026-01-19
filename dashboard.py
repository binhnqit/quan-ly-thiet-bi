import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống AI 3651 - V53", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v53():
    try:
        # Thêm mã phá cache để lấy đủ 3.651 dòng
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu, ép tất cả về kiểu Chuỗi (str) ngay từ đầu để tránh lỗi .upper()
        df_raw = pd.read_csv(url, header=None, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- CHIẾN THUẬT QUÉT DÒNG TIÊU ĐỀ ---
        header_idx = -1
        for i in range(min(15, len(df_raw))):
            # Chuyển dòng thành danh sách chuỗi, viết hoa để so khớp
            row_values = [str(x).upper() for x in df_raw.iloc[i].values]
            line_str = " ".join(row_values)
            if 'MÃ' in line_str or 'NGÀY' in line_str or 'LÝ DO' in line_str:
                header_idx = i
                break
        
        if header_idx == -1:
            return None

        # Thiết lập Tiêu đề cột chuẩn
        headers = [str(c).strip().upper() for c in df_raw.iloc[header_idx]]
        df = df_raw.iloc[header_idx+1:].copy()
        df.columns = headers
        
        # Tìm các cột quan trọng (Dò theo từ khóa)
        def find_col(keywords):
            for k in keywords:
                for name in headers:
                    if k in name: return name
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
        
        # Chuyển đổi ngày tháng (Chống lỗi định dạng)
        new_df['NGÀY_GỐC'] = pd.to_datetime(df[c_ng], dayfirst=True, errors='coerce')
        
        # Chỉ giữ lại dòng có mã máy
        new_df = new_df[new_df['MÃ_MÁY'] != ""].copy()
        
        # Tạo cột Năm/Tháng phục vụ bộ lọc
        new_df['NĂM'] = new_df['NGÀY_GỐC'].dt.year.fillna(0).astype(int)
        new_df['THÁNG_SO'] = new_df['NGÀY_GỐC'].dt.month.fillna(0).astype(int)
        
        return new_df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🚀 CẬP NHẬT 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v53()
    
    if data is not None:
        st.success(f"✅ Đã nhận {len(data)} dòng")
        
        # Bộ lọc Năm
        list_năm = sorted([y for y in data['NĂM'].unique() if y > 0], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + list_năm)
        
        # Bộ lọc Tháng
        sel_month = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])
        
        # Thực hiện lọc
        df_filtered = data.copy()
        if sel_year != "Tất cả":
            df_filtered = df_filtered[df_filtered['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_filtered = df_filtered[df_filtered['THÁNG_SO'] == m_num]
    else:
        st.error("Chưa tìm thấy dữ liệu hoặc link lỗi.")
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    tab1, tab2 = st.tabs(["🔍 TÌM KIẾM CHI TIẾT", "📊 THỐNG KÊ"])
    
    with tab1:
        st
