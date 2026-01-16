import streamlit as st
import pandas as pd
import plotly.express as px
import math
import base64

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .guide-box { background-color: #f0f7ff; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A; }
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

# --- SIDEBAR: BỘ LỌC CHIẾN LƯỢC ---
with st.sidebar:
    st.title("🛡️ BỘ LỌC AI")
    list_years = sorted(df['NĂM'].unique(), reverse=True)
    sel_year = st.selectbox("📅 Chọn Năm", list_years)
    
    list_vung = sorted(df['VÙNG_MIỀN'].unique())
    sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
    
    df_temp = df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))]
    list_months = sorted(df_temp['THÁNG'].unique())
    sel_months = st.multiselect("📆 Chọn Tháng", list_months, default=list_months)
    
    st.divider()
    # TÍNH NĂNG XUẤT CSV (Để sếp lưu về máy nhanh nhất)
    if not df_temp.empty:
        csv = df_temp.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📄 Tải Báo Cáo (CSV)",
            data=csv,
            file_name=f'Bao_cao_tai_san_{sel_year}.csv',
            mime='text/csv',
        )

# Lọc dữ liệu chính (ĐÃ FIX LỖI VÙNG_MIỀF)
df_filtered = df[(df['NĂM'] == sel_year) & 
                 (df['THÁNG'].isin(sel_months)) & 
                 (df['VÙNG_MIỀN'].isin(sel_vung))]

# --- GIAO DIỆN TABS ---
tab1, tab2 = st.tabs(["📊 Báo Cáo Chiến Lược", "📖 Hướng Dẫn Vận Hành"])

with tab1:
    st.title("🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI")
    
    # KPI ROWS
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    
    # Tính dự báo ngân sách
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    n_m = len(sel_months) if sel_months else 1
    est_budget = sum([math.ceil((v/n_m)*1.2)*500000 for v in forecast_counts.values])
    
    c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    c3.metric("Số máy Đỏ (Cần thanh lý)", f"{(df['MÃ_MÁY'].value_counts() >= 4).sum()}")

    st.divider()

    # CHATBOT AI TRUY LỤC (QUÉT TOÀN BỘ DATA)
    st.subheader("💬 Trợ lý Tra cứu Hồ sơ bệnh án")
    user_msg = st.text_input("Nhập mã máy (Ví dụ: 3534):", placeholder="Gõ số máy vào đây...")
    if user_msg:
        import re
        m = re.search(r'\d+', user_msg)
        if m:
            code = m.group()
            h = df[df['MÃ_MÁY'] == code].sort_values('NGAY_FIX', ascending=False)
            if not h.empty:
                st.info(f"🔍 Tìm thấy {len(h)} lần sửa cho máy {code}:")
                st.table(h[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
            else: st.error("❌ Không tìm thấy dữ liệu máy này.")

    st.divider()

    # BIỂU ĐỒ
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ hỏng theo Vùng")
        st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5, color_discrete_sequence=px.colors.qualitative.Set3), use_container_width=True)
    with col_r:
        st.subheader("🛠️ Top 10 lỗi phổ biến nhất")
        st.plotly_chart(px.bar(df_filtered['LÝ_DO_HỎNG'].value_counts().head(10), orientation='h', color_discrete_sequence=['#1E3A8A']), use_container_width=True)

    # DANH SÁCH SỨC KHỎE
    st.subheader("🌡️ Theo dõi Sức khỏe Hệ thống")
    health = df['MÃ_MÁY'].value_counts().reset_index()
    health.columns = ['Mã Máy', 'Lượt hỏng']
    health['Trạng thái'] = health['Lượt hỏng'].apply(lambda x: "🔴 Nguy kịch" if x>=4 else ("🟠 Yếu" if x==3 else "🟢 Tốt"))
    st.dataframe(health.head(20), use_container_width=True)

with
