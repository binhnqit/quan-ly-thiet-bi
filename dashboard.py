import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# 1. CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP
st.set_page_config(page_title="Hệ Thống Quản Trị V88", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f1f3f6; }
    .stMetric { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 5px solid #1E3A8A; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v88():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu thô
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("Chưa xác định")
        
        final_data = []
        for _, row in df_raw.iterrows():
            row_str = " ".join(row.values.astype(str))
            # Bỏ qua dòng tiêu đề
            if "Mã số" in row_str or "Ngày" in row_str: continue
            
            # BIÓC TÁCH DỮ LIỆU BẰNG REGEX (THÔNG MINH HƠN)
            # Tìm ngày (dd/mm/yyyy)
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_str)
            ngay = date_match.group(1) if date_match else "01/01/2026"
            
            # Tìm Mã máy (thường là số 3-5 chữ số đứng riêng lẻ)
            ma_match = re.findall(r'\b\d{3,5}\b', row_str)
            ma = ma_match[0] if ma_match else "Chưa rõ"
            
            # Khách hàng và Linh kiện: Lấy dựa trên vị trí cột thực tế (ép cột)
            # Theo hình ảnh, cột 2 thường là Khách, cột 3 là Linh kiện/Lý do
            kh = str(row.iloc[2]).strip() if len(row) > 2 else "Chưa xác định"
            lk = str(row.iloc[3]).strip() if len(row) > 3 else "Chưa xác định"
            
            final_data.append([ngay, ma, kh, lk])

        df = pd.DataFrame(final_data, columns=['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN'])
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY_DT'].dt.month.fillna(0).astype(int)
        
        # PHÂN VÙNG MIỀN (Fix image_eb9d08)
        def phan_vung(kh):
            v = str(kh).upper()
            if any(x in v for x in ['HN', 'NỘI', 'BẮC', 'PHÚ', 'SƠN', 'THÁI']): return 'MIỀN BẮC'
            if any(x in v for x in ['ĐÀ NẴNG', 'HUẾ', 'TRUNG', 'VINH', 'QUẢNG']): return 'MIỀN TRUNG'
            return 'MIỀN NAM'
        df['VÙNG'] = df['KHÁCH_HÀNG'].apply(phan_vung)
        
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR CONTROL ---
data = load_data_v88()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063226.png", width=80)
    st.title("QUẢN TRỊ TÀI SẢN V88")
    if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if data is not None:
        years = sorted(data['NĂM'].unique(), reverse=True)
        sel_y = st.selectbox("📅 Năm", ["Tất cả"] + years)
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("📆 Tháng", months)

        # Logic lọc
        df_filtered = data.copy()
        if sel_y != "Tất cả": df_filtered = df_filtered[df_filtered['NĂM'] == sel_y]
        if sel_m != "Tất cả":
            m_val = int(sel_m.replace("Tháng ", ""))
            df_filtered = df_filtered[df_filtered['THÁNG'] == m_val]

# --- DASHBOARD CHÍNH ---
if data is not None:
    # KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_filtered):,}")
    c2.metric("Thiết bị lỗi", f"{df_filtered['MÃ_MÁY'].nunique():,}")
    
    # Tính toán máy hỏng tái diễn chuyên sâu
    re_fail = df_filtered['MÃ_MÁY'].value_counts()
    re_fail = re_fail[re_fail > 1]
    c3.metric("Máy hỏng tái diễn", len(re_fail))
    c4.metric("Khách hàng", df_filtered['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3, tab4 = st.tabs(["📈 BÁO CÁO", "⚠️ DANH SÁCH ĐEN", "🔍 TRA CỨU", "📋 DỮ LIỆU GỐC"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("**Top 10 Linh kiện lỗi nhiều nhất**")
            lk_counts = df_filtered[df_filtered['LINH_KIỆN'] != "Chưa xác định"]['LINH_KIỆN'].value_counts().head(10)
            fig = px.bar(lk_counts, orientation='h', color=lk_counts.values, color_continuous_scale='Turbo
