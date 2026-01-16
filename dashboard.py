import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Laptop Management System PRO", layout="wide")

PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_pro():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # Xử lý vùng miền
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa ghi chú").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0]
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        
        # Loại bỏ rác
        df = df[df['MÃ_MÁY'] != 'nan']
        df = df[~df['MÃ_MÁY'].str.contains("STT|MÃ|THEO", na=False)]
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

df = load_data_pro()

# --- SIDEBAR CHUYÊN NGHIỆP ---
with st.sidebar:
    st.title("⚙️ QUẢN TRỊ")
    search = st.text_input("🔍 Tra cứu máy/linh kiện", placeholder="Nhập mã máy...")
    
    # Lọc theo tháng
    st.subheader("📅 Khoảng thời gian")
    month_filter = st.multiselect("Chọn tháng báo cáo", 
                                  options=[11, 12, 1, 2], 
                                  default=[12, 1],
                                  format_func=lambda x: f"Tháng {x}")
    
    selected_vung = st.multiselect("📍 Khu vực", ["Miền Bắc", "Miền Trung", "Miền Nam"], default=["Miền Bắc", "Miền Nam"])
    
    st.divider()
    st.success(f"Dữ liệu trực tuyến: {len(df)} dòng")

# --- LOGIC LỌC ---
mask = df['VÙNG_MIỀN'].isin(selected_vung)
if month_filter:
    mask = mask & (df['NGAY_FIX'].dt.month.isin(month_filter))
if search:
    mask = mask & (df['MÃ_MÁY'].str.contains(search, case=False) | df['LÝ_DO_HỎNG'].str.contains(search, case=False))

df_filtered = df[mask]

# --- GIAO DIỆN CHÍNH ---
st.markdown("# 🛡️ Hệ Thống Quản Trị Thiết Bị Tập Đoàn")

# KPIs Hàng đầu
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Tổng lượt tiếp nhận", f"{len(df_filtered):,}")
with c2:
    st.metric("Tài sản đang lỗi", f"{df_filtered['MÃ_MÁY'].nunique():,}")
with c3:
    repeat_df = df_filtered['MÃ_MÁY'].value_counts()
    critical_count = len(repeat_df[repeat_df >= 3])
    st.metric("🚨 Máy hỏng nặng (>=3 lần)", critical_count, delta="Cần thanh lý", delta_color="inverse")
with c4:
    st.metric("Lý do phổ biến nhất", df_filtered['LÝ_DO_HỎNG'].mode()[0] if not df_filtered.empty else "N/A")

st.divider()

# BIỂU ĐỒ PHÂN TÍCH
col_left, col_right = st.columns([6, 4])

with col_left:
    st.subheader("🛠️ Top 15 Linh kiện tiêu tốn ngân sách (Cột D)")
    reason_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(15).reset_index()
    fig_reason = px.bar(reason_counts, x='count', y='LÝ_DO_HỎNG', orientation='h', 
                       text_auto=True, color='count', color_continuous_scale='Reds')
    fig_reason.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_reason, use_container_width=True)

with col_right:
    st.subheader("📈 Tỷ lệ phát sinh lỗi theo Vùng")
    vung_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
    fig_pie = px.pie(vung_data, values='count', names='VÙNG_MIỀN', hole=0.5,
                    color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
    st.plotly_chart(fig_pie, use_container_width=True)

# PHÂN TÍCH CHUYÊN SÂU
st.divider()
ca1, ca2 = st.columns(2)

with ca1:
    st.subheader("🚩 Danh sách Máy hỏng lặp lại (Báo động)")
    bad_machines = repeat_df[repeat_df >= 2].reset_index()
    bad_machines.columns = ['Mã Máy', 'Số lần hỏng']
    st.dataframe(bad_machines.head(10), use_container_width=True)

with ca2:
    st.subheader("📅 Biến động ca hỏng theo ngày")
    trend = df_filtered.dropna(subset=['NGAY_FIX']).groupby(df_filtered['NGAY_FIX'].dt.date).size().reset_index()
    trend.columns = ['Ngày', 'Số ca']
    fig_trend = px.line(trend, x='Ngày', y='Số ca', markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# CHI TIẾT DỮ LIỆU
st.subheader("📋 Nhật ký sửa chữa chi tiết")
st.dataframe(df_filtered[['MÃ_MÁY', 'VÙNG_MIỀN', 'LÝ_DO_HỎNG', 'COL_6']].tail(50), use_container_width=True)
