import streamlit as st
import pandas as pd
import plotly.express as px
import math

# 1. CẤU HÌNH GIAO DIỆN (GIỮ NGUYÊN STYLE PRO)
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border: 1px solid #e2e8f0;
        border-top: 5px solid #1E3A8A;
    }
    .main-title { color: #1E3A8A; font-weight: 800; text-align: center; font-size: 2.5rem; margin-bottom: 20px; }
    .section-header { color: #1E3A8A; font-weight: 700; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU (TỔNG 3.976 DÒNG)
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(PUBLISHED_URL)
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"
        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0].str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except: return pd.DataFrame()

df = load_data()

# --- BỘ LỌC CHIẾN LƯỢC (SIDEBAR) ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    list_years = sorted(df['NĂM'].unique(), reverse=True)
    sel_year = st.selectbox("Chọn Năm", list_years)
    list_vung = sorted(df['VÙNG_MIỀN'].unique())
    sel_vung = st.multiselect("Chọn Miền", list_vung, default=list_vung)
    df_temp = df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))]
    list_months = sorted(df_temp['THÁNG'].unique())
    sel_months = st.multiselect("Chọn Tháng", list_months, default=list_months)

df_filtered = df[(df['NĂM'] == sel_year) & (df['THÁNG'].isin(sel_months)) & (df['VÙNG_MIỀN'].isin(sel_vung))]

# --- GIAO DIỆN CHÍNH ---
st.markdown('<p class="main-title">🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Báo Cáo Chiến Lược", "⚡ Ưu Tiên Mua Sắm", "📖 Hướng Dẫn"])

with tab1:
    # KHỐI THẺ KPI (GIỮ ĐÚNG GIAO DIỆN SẾP CHỌN)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    
    n_m = len(sel_months) if sel_months else 1
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    est_budget = sum([math.ceil((v/n_m)*1.2)*500000 for v in forecast_counts.values])
    c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    
    bad_assets = (df['MÃ_MÁY'].value_counts() >= 4).sum()
    c3.metric("Máy Nguy kịch (Đỏ)", f"{bad_assets}")

    st.divider()
    
    # TRA CỨU HỒ SƠ
    st.subheader("💬 Trợ lý Tra cứu Hồ sơ")
    ma_may = st.text_input("Gõ mã máy (VD: 3534):", key="search_main")
    if ma_may:
        h = df[df['MÃ_MÁY'] == ma_may.strip()].sort_values('NGAY_FIX', ascending=False)
        if not h.empty:
            st.info(f"Tìm thấy {len(h)} lần sửa cho máy {ma_may}")
            st.table(h[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
        else:
            st.error(f"Không tìm thấy mã máy {ma_may} trong hệ thống.")

    # BIỂU ĐỒ TRỰC QUAN
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ theo Vùng")
        st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5), use_container_width=True)
    with col_r:
        st.subheader("🛠️ Top 10 lỗi phổ biến")
        st.plotly_chart(px.bar(df_filtered['LÝ_DO_HỎNG'].value_counts().head(10), orientation='h'), use_container_width=True)

with tab2:
    st.subheader("📋 Danh Sách Ưu Tiên Mua Sắm")
    
    # Thuật toán phân cấp ưu tiên
    def get_priority(row):
        m_code = str(row['MÃ_MÁY'])
        h_count = len(df[df['MÃ_MÁY'] == m_code])
        if any(x in str(row['LÝ_DO_HỎNG']) for x in ['Màn', 'Main', 'Nguồn']): return "🔴 KHẨN CẤP"
        if h_count >= 4: return "🟠 CAO"
        return "🟢 BÌNH THƯỜNG"

    if not df_filtered.empty:
        df_p = df_filtered.copy()
        df_p['ƯU TIÊN'] = df_p.apply(get_priority, axis=1)
        st.dataframe(df_p[['ƯU TIÊN', 'MÃ_MÁY', 'LÝ_DO_HỎNG', 'NGAY_FIX', 'VÙNG_MIỀN']], use_container_width=True)
    else:
        st.warning("Vui lòng chọn dữ liệu để phân tích ưu tiên.")

with tab3:
    st.info("### 📘 Quy trình vận hành chuẩn")
    st.write("1. Luôn tra cứu hồ sơ tại Tab 1 trước khi quyết định sửa chữa.")
    st.write("2. Ưu tiên cấp ngân sách cho các máy nằm trong diện KHẨN CẤP tại Tab 2.")
    st.write("3. Nhấn Ctrl + P để in báo cáo khi cần trình ký.")
