import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 - V48", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v48():
    try:
        # Ép tải mới
        url = f"{DATA_URL}&cache={time.time()}"
        df = pd.read_csv(url, on_bad_lines='skip', dtype=str)
        
        # Nếu dòng 1 bị trống, tự động lấy dòng tiếp theo làm tiêu đề
        if df.columns[0].startswith('Unnamed'):
            df.columns = df.iloc[0]
            df = df[1:]

        # Làm sạch tên cột để đối chiếu
        cols = [str(c).strip().upper() for c in df.columns]
        df.columns = cols

        # TÌM CỘT THÔNG MINH (Dò theo từ khóa)
        def find_col(keywords):
            for k in keywords:
                for c in df.columns:
                    if k in c: return c
            return None

        c_ma = find_col(['MÃ', 'MA', 'ID', 'DEVICE'])
        c_ly = find_col(['LÝ DO', 'LY DO', 'NỘI DUNG', 'NOI DUNG', 'CHI TIẾT', 'LOI'])
        c_ng = find_col(['NGÀY', 'NGAY', 'DATE', 'TIME'])

        if not c_ma or not c_ng:
            st.error(f"❌ AI tìm thấy các cột: {list(df.columns)}. Nhưng không thấy cột nào tên là 'MÃ' hoặc 'NGÀY'. Sếp sửa lại tiêu đề dòng 1 nhé!")
            return None

        # Chuyển đổi dữ liệu
        new_df = pd.DataFrame()
        new_df['MÃ_MÁY'] = df[c_ma].str.split('.').str[0].str.strip()
        new_df['LÝ_DO'] = df[c_ly].fillna("Trống")
        new_df['NGÀY_GỐC'] = pd.to_datetime(df[c_ng], dayfirst=True, errors='coerce')
        
        # Xử lý Năm/Tháng
        new_df['NĂM'] = new_df['NGÀY_GỐC'].dt.year.fillna(2026).astype(int)
        new_df['THÁNG'] = new_df['NGÀY_GỐC'].dt.month.fillna(1).astype(int)
        
        return new_df
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN")
    if st.button('🚀 KẾT NỐI 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v48()
    if data is not None:
        st.success(f"✅ Đã nhận {len(data)} dòng")
        
        # Lọc Năm và Tháng
        list_năm = ["Tất cả"] + sorted(data['NĂM'].unique().tolist(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_năm)
        
        list_thang = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", list_thang)
        
        # Áp dụng lọc
        df_final = data.copy()
        if sel_year != "Tất cả":
            df_final = df_final[df_final['NĂM'] == sel_year]
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
        search = st.text_input("Gõ mã máy hoặc lỗi để truy lục lịch sử:")
        if search:
            # Tìm trong toàn bộ dữ liệu (data) thay vì df_final (dữ liệu đã lọc)
            res = data[data['MÃ_MÁY'].str.contains(search, na=False, case=False) | 
                       data['LÝ_DO'].str.contains(search, na=False, case=False)]
            st.dataframe(res[['NGÀY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)
    
    with t2:
        st.write(f"📂 Đang xem: {sel_month} / {sel_year}")
        st.metric("Tổng số ca", len(df_final))
        st.bar_chart(df_final['LÝ_DO'].value_counts().head(10))
