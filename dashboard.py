import streamlit as st
import pandas as pd
import plotly.express as px
import math
from datetime import datetime

# 1. CẤU HÌNH GIAO DIỆN GỐC (GIỮ NGUYÊN STYLE CARDS)
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
    .main-title { color: #1E3A8A; font-weight: 800; text-align: center; font-size: 2.2rem; margin-bottom: 20px; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU
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
current_year = datetime.now().year

# --- SIDEBAR & TẢI CSV ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    list_years = sorted(df['NĂM'].unique(), reverse=True)
    sel_year = st.selectbox("📅 Chọn Năm", list_years, index=list_years.index(current_year) if current_year in list_years else 0)
    
    list_vung = sorted(df['VÙNG_MIỀN'].unique())
    sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
    
    df_temp = df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))]
    list_months = sorted(df_temp['THÁNG'].unique())
    sel_months = st.multiselect("📆 Chọn Tháng", list_months, default=list_months)
    
    st.divider()
    if not df_temp.empty:
        csv = df_temp.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 Tải Báo Cáo CSV", data=csv, file_name=f'Bao_cao_{sel_year}.csv', mime='text/csv')

# Lọc dữ liệu chính theo bộ lọc
df_filtered = df[(df['NĂM'] == sel_year) & (df['THÁNG'].isin(sel_months)) & (df['VÙNG_MIỀN'].isin(sel_vung))]

# --- THÔNG BÁO ĐẨY (PUSH NOTIFICATION) ---
# Kiểm tra trong tập dữ liệu lọc có máy nào mới rơi vào danh sách hỏng >= 4 lần không
machine_counts = df['MÃ_MÁY'].value_counts()
critical_machines = machine_counts[machine_counts >= 4].index.tolist()
current_filter_critical = df_filtered[df_filtered['MÃ_MÁY'].isin(critical_machines)]['MÃ_MÁY'].unique()

if len(current_filter_critical) > 0:
    st.toast(f"🚨 CẢNH BÁO: Phát hiện {len(current_filter_critical)} thiết bị Nguy kịch trong bộ lọc hiện tại!", icon="🔥")
    with st.expander("⚠️ Danh sách máy cần kiểm tra gấp"):
        st.error(f"Các máy sau đã hỏng trên 4 lần: {', '.join(current_filter_critical[:10])}...")

# --- GIAO DIỆN CHÍNH ---
st.markdown('<p class="main-title">🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Báo Cáo Chiến Lược", "⚡ Ưu Tiên Mua Sắm", "📖 Hướng Dẫn"])

with tab1:
    # 3 THẺ KPI GIAO DIỆN GỐC
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    
    n_m = len(sel_months) if sel_months else 1
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    est_budget = sum([math.ceil((v/n_m)*1.2)*500000 for v in forecast_counts.values])
    c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    
    c3.metric("Máy Nguy kịch (Health < 30%)", f"{len(current_filter_critical)}")

    st.divider()

    # THỐNG KÊ LINH KIỆN HƯ HỎNG (MỚI)
    st.subheader("🛠️ Thống kê linh kiện hư hỏng theo bộ lọc")
    
    # Hàm phân loại linh kiện từ mô tả lỗi
    def classify_part(reason):
        reason = reason.lower()
        if 'pin' in reason: return 'Pin'
        if 'màn' in reason or 'lcd' in reason: return 'Màn hình'
        if 'phím' in reason or 'keyboard' in reason: return 'Bàn phím'
        if 'nguồn' in reason or 'sạc' in reason: return 'Bộ nguồn/Sạc'
        if 'ổ cứng' in reason or 'ssd' in reason or 'hhd' in reason: return 'Ổ cứng'
        if 'main' in reason or 'bo mạch' in reason: return 'Mainboard'
        return 'Linh kiện khác'

    df_filtered['LINH_KIỆN'] = df_filtered['LÝ_DO_HỎNG'].apply(classify_part)
    part_stats = df_filtered['LINH_KIỆN'].value_counts().reset_index()
    part_stats.columns = ['Linh kiện', 'Số lượng hỏng']

    col_chart1, col_chart2 = st.columns([6, 4])
    with col_chart1:
        fig_parts = px.bar(part_stats, x='Số lượng hỏng', y='Linh kiện', orientation='h', 
                           title="Biểu đồ phân loại linh kiện thay thế",
                           color='Số lượng hỏng', color_continuous_scale='RdBu')
        st.plotly_chart(fig_parts, use_container_width=True)
    with col_chart2:
        st.write("**Bảng chi tiết linh kiện:**")
        st.dataframe(part_stats, use_container_width=True)

    st.divider()
    
    # BẢN ĐỒ PHÂN VÙNG RỦI RO
    st.subheader("🗺️ Bản đồ rủi ro theo vùng miền")
    col_map_l, col_map_r = st.columns(2)
    with col_map_l:
        st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5, title="Tỷ lệ ca hỏng"), use_container_width=True)
    with col_map_r:
        risk_df = df_filtered.groupby('VÙNG_MIỀN').size().reset_index(name='Số ca')
        st.plotly_chart(px.bar(risk_df, x='VÙNG_MIỀN', y='Số ca', color='VÙNG_MIỀN', title="Số ca hỏng chi tiết"), use_container_width=True)

with tab2:
    st.header("📋 Hệ Thống Ưu Tiên Mua Sắm & Sửa Chữa")
    # ... (Giữ nguyên logic Tab 2 như bản cũ sếp đã duyệt)
    if not df_filtered.empty:
        df_p = df_filtered.copy()
        def get_priority(row):
            if any(x in str(row['LÝ_DO_HỎNG']) for x in ['Màn', 'Main', 'Nguồn']): return "🔴 KHẨN CẤP"
            if str(row['MÃ_MÁY']) in critical_machines: return "🟠 CAO"
            return "🟢 BÌNH THƯỜNG"
        df_p['ƯU TIÊN'] = df_p.apply(get_priority, axis=1)
        st.dataframe(df_p[['ƯU TIÊN', 'MÃ_MÁY', 'LÝ_DO_HỎNG', 'NGAY_FIX', 'VÙNG_MIỀN']], use_container_width=True)

with tab3:
    st.info("### 📘 Quy trình vận hành chuẩn")
    st.write("1. **Theo dõi thông báo:** Nếu thấy Toast cảnh báo hiện lên, kiểm tra ngay danh sách máy Nguy kịch.")
    st.write("2. **Duyệt mua sắm:** Sử dụng biểu đồ 'Thống kê linh kiện' để biết cần nhập hàng loại nào về kho nhiều nhất.")
