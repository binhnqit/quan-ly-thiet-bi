import streamlit as st
import pandas as pd
import plotly.express as px
import math

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 4px solid #1E3A8A; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .priority-urgent { background-color: #ffebee; color: #c62828; padding: 5px; border-radius: 5px; font-weight: bold; }
    h1 { color: #1E3A8A; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_final():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
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
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_final()

# --- SIDEBAR BỘ LỌC ---
with st.sidebar:
    st.title("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if not df.empty:
        list_years = sorted(df['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years)
        
        list_vung = sorted(df['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        
        df_temp = df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))]
        list_months = sorted(df_temp['THÁNG'].unique())
        sel_months = st.multiselect("📆 Chọn Tháng", list_months, default=list_months)
    else:
        sel_year, sel_vung, sel_months = None, [], []

# Lọc dữ liệu chính
df_filtered = df[(df['NĂM'] == sel_year) & 
                 (df['THÁNG'].isin(sel_months)) & 
                 (df['VÙNG_MIỀN'].isin(sel_vung))]

# --- GIAO DIỆN CHÍNH ---
tab1, tab2, tab3 = st.tabs(["📊 Báo Cáo Chiến Lược", "⚡ Ưu Tiên Mua Sắm", "📖 Hướng Dẫn"])

with tab1:
    st.title("🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI")
    
    # KPI 
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    
    # Tính dự báo chi phí an toàn (Fix lỗi n_m)
    n_m = len(sel_months) if sel_months else 1
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    est_budget = sum([math.ceil((v/n_m)*1.2)*500000 for v in forecast_counts.values])
    c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    
    bad_assets = (df['MÃ_MÁY'].value_counts() >= 4).sum()
    c3.metric("Số máy Nguy kịch (Đỏ)", f"{bad_assets} máy")

    st.divider()
    
    # CHATBOT TRUY LỤC
    st.subheader("💬 Trợ lý Tra cứu Hồ sơ (Toàn hệ thống)")
    ma_may = st.text_input("Gõ mã máy (VD: 3534):")
    if ma_may:
        h = df[df['MÃ_MÁY'] == ma_may.strip()].sort_values('NGAY_FIX', ascending=False)
        if not h.empty:
            st.success(f"Tìm thấy {len(h)} lần sửa cho máy {ma_may}:")
            st.dataframe(h[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']], use_container_width=True)
        else:
            st.error("Không tìm thấy dữ liệu.")

    # BIỂU ĐỒ
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ theo Vùng")
        st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5), use_container_width=True)
    with col_r:
        st.subheader("🛠️ Top 10 lỗi phổ biến")
        st.plotly_chart(px.bar(df_filtered['LÝ_DO_HỎNG'].value_counts().head(10), orientation='h'), use_container_width=True)

with tab2:
    st.header("📋 Danh Sách Ưu Tiên Mua Sắm &
