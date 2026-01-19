import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 - V49", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v49():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc file thô không lấy tiêu đề trước
        df_raw = pd.read_csv(url, header=None, on_bad_lines='skip', dtype=str)
        
        # --- CHIẾN THUẬT QUÉT DÒNG TIÊU ĐỀ ---
        # AI sẽ thử từng dòng để tìm xem dòng nào chứa từ khóa quan trọng
        header_idx = 0
        found = False
        for i in range(len(df_raw)):
            row_content = " ".join(df_raw.iloc[i].astype(str).upper())
            if 'MÃ' in row_content or 'NGÀY' in row_content:
                header_idx = i
                found = True
                break
        
        if not found:
            st.error("❌ AI đã quét 5 dòng đầu nhưng không thấy tiêu đề 'Mã máy' hay 'Ngày'. Sếp kiểm tra lại xem cột đó có nằm trong 5 dòng đầu không nhé!")
            return None

        # Thiết lập lại DataFrame từ dòng tiêu đề tìm được
        df = df_raw.iloc[header_idx+1:].copy()
        df.columns = [str(c).strip().upper() for c in df_raw.iloc[header_idx]]
        
        # Tìm các cột cần thiết
        def find_col(keywords):
            for k in keywords:
                for c in df.columns:
                    if k in str(c): return c
            return None

        c_ma = find_col(['MÃ', 'MA', 'ID'])
        c_ly = find_col(['LÝ DO', 'NỘI DUNG', 'CHI TIẾT', 'LOI'])
        c_ng = find_col(['NGÀY', 'NGAY', 'DATE'])

        if not c_ma or not c_ng:
            st.warning(f"Cột tìm thấy: {list(df.columns)}")
            return None

        # Làm sạch và chuyển đổi
        new_df = pd.DataFrame()
        new_df['MÃ_MÁY'] = df[c_ma].str.split('.').str[0].str.strip()
        new_df['LÝ_DO'] = df[c_ly].fillna("Trống")
        new_df['NGÀY_GỐC'] = pd.to_datetime(df[c_ng], dayfirst=True, errors='coerce')
        
        # Bỏ dòng trống
        new_df = new_df.dropna(subset=['MÃ_MÁY'])
        
        new_df['NĂM'] = new_df['NGÀY_GỐC'].dt.year.fillna(2026).astype(int)
        new_df['THÁNG'] = new_df['NGÀY_GỐC'].dt.month.fillna(1).astype(int)
        
        return new_df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🚀 KẾT NỐI 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v49()
    if data is not None:
        st.success(f"✅ Đã nhận {len(data)} dòng")
        list_year = ["Tất cả"] + sorted(data['NĂM'].unique().tolist(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_year)
        
        list_month = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", list_month)
        
        df_final = data.copy()
        if sel_year != "Tất cả": df_final = df_final[df_final['NĂM'] == sel_year]
        if sel_month != "Tất cả": 
            m_num = int(sel_month.split(" ")[1])
            df_final = df_final[df_final['THÁNG'] == m_num]
    else:
        df_final = pd.DataFrame()

# --- GIAO DIỆN ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if not df_final.empty:
    t1, t2 = st.tabs(["🔍 TÌM KIẾM CHUẨN", "📊 THỐNG KÊ"])
    
    with t1:
        search = st.text_input("Gõ mã máy để xem lịch sử sửa chữa:")
        if search:
            res = data[data['MÃ_MÁY'].str.contains(search, na=False, case=False)]
            st.info(f"Tìm thấy {len(res)} kết quả.")
            st.dataframe(res[['NGAY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)
    
    with t2:
        st.metric("Tổng ca sửa tháng này", len(df_final))
        st.bar_chart(df_final['LÝ_DO'].value_counts().head(10))
