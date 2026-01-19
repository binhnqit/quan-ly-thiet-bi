import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 - V54", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v54():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu thô, bỏ qua các dòng lỗi
        df = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        if df.empty: return None

        # TỰ ĐỘNG NHẬN DIỆN CỘT THEO VỊ TRÍ (Phòng trường hợp tiêu đề sai)
        # Thông thường: Cột 1 là Mã, Cột 3 là Lý do, Cột 6 là Ngày (theo file sếp)
        new_df = pd.DataFrame()
        
        # Thử tìm cột theo tên trước
        cols = [str(c).upper() for c in df.columns]
        
        idx_ma = next((i for i, c in enumerate(cols) if 'MÃ' in c or 'MA' in c), 1)
        idx_ly = next((i for i, c in enumerate(cols) if 'LÝ DO' in c or 'NỘI DUNG' in c), 3)
        idx_ng = next((i for i, c in enumerate(cols) if 'NGÀY' in c or 'NGAY' in c), 6)

        new_df['MÃ_MÁY'] = df.iloc[:, idx_ma].astype(str).str.split('.').str[0].str.strip()
        new_df['LÝ_DO'] = df.iloc[:, idx_ly].astype(str).str.strip()
        new_df['NGÀY_GỐC'] = pd.to_datetime(df.iloc[:, idx_ng], dayfirst=True, errors='coerce')
        
        # Làm sạch dữ liệu rác
        new_df = new_df[new_df['MÃ_MÁY'] != ""].copy()
        new_df['NĂM'] = new_df['NGÀY_GỐC'].dt.year.fillna(0).astype(int)
        new_df['THÁNG_SO'] = new_df['NGAY_GỐC'].dt.month.fillna(0).astype(int)
        
        return new_df
    except Exception as e:
        st.error(f"Lỗi kỹ thuật: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🚀 KẾT NỐI DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v54()
    
    if data is not None:
        st.success(f"✅ Đã nhận {len(data)} dòng")
        
        years = sorted([y for y in data['NĂM'].unique() if y > 0], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + years)
        
        sel_month = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])
        
        df_filtered = data.copy()
        if sel_year != "Tất cả":
            df_filtered = df_filtered[df_filtered['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_filtered = df_filtered[df_filtered['THÁNG_SO'] == m_num]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    tab1, tab2 = st.tabs(["🔍 TÌM KIẾM CHÍNH XÁC", "📊 THỐNG KÊ"])
    
    with tab1:
        q = st.text_input("Nhập Mã thiết bị (VD: 3534):")
        if q:
            # Tìm trên toàn bộ data gốc
            res = data[data['MÃ_MÁY'].str.contains(q, na=False, case=False)]
            st.dataframe(res[['NGÀY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)
            
    with tab2:
        st.metric("Tổng ca sửa", len(df_filtered))
        st.bar_chart(df_filtered['LÝ_DO'].value_counts().head(10))
else:
    st.warning("⚠️ Đang kết nối với Google Sheets... Sếp vui lòng đợi 5 giây hoặc nhấn 'KẾT NỐI' ở bên trái.")
