import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Hệ thống Quản trị Laptop Enterprise", layout="wide")

PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_expert_data():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # 1. Tiền xử lý dữ liệu chuẩn
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa ghi chú").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0]
        
        # Xử lý thời gian chuyên sâu
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX']) # Chỉ lấy những dòng có ngày để báo cáo thời gian
        df['YEAR'] = df['NGAY_FIX'].dt.year.astype(int)
        df['MONTH'] = df['NGAY_FIX'].dt.month.astype(int)
        
        # Loại bỏ rác
        df = df[df['MÃ_MÁY'] != 'nan']
        df = df[~df['MÃ_MÁY'].str.contains("STT|MÃ|THEO", na=False)]
        return df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame()

df = load_expert_data()

# --- SIDEBAR: QUẢN TRỊ THỜI GIAN ---
with st.sidebar:
    st.header("🕒 Quản trị Thời gian")
    
    # Lọc Năm
    list_years = sorted(df['YEAR'].unique(), reverse=True)
    selected_year = st.selectbox("Chọn Năm báo cáo", list_years)
    
    # Lọc Tháng (Chỉ hiện các tháng có trong năm đã chọn)
    df_year = df[df['YEAR'] == selected_year]
    list_months = sorted(df_year['MONTH'].unique())
    selected_months = st.multiselect("Chọn Tháng", options=list_months, default=list_months, format_func=lambda x: f"Tháng {x}")
    
    st.header("📍 Khu vực")
    list_vung = ["Miền Bắc", "Miền Trung", "Miền Nam"]
    selected_vung = st.multiselect("Vùng miền", list_vung, default=list_vung)
    
    st.divider()
    st.info("💡 Chế độ: Chuyên gia 15 năm kinh nghiệm")

# LỌC DỮ LIỆU
mask = (df['YEAR'] == selected_year) & (df['MONTH'].isin(selected_months)) & (df['VÙNG_MIỀN'].isin(selected_vung))
df_filtered = df[mask]

# --- GIAO DIỆN ---
st.title("🛡️ Enterprise IT Asset Management Dashboard")

# 1. TRUY VẾT MÃ MÁY (DRILL-DOWN)
st.markdown("### 🔍 Truy vết "Hồ sơ bệnh án" thiết bị")
search_query = st.text_input("Nhập mã máy (VD: 2498)", key="expert_search").strip()
if search_query:
    history = df[df['MÃ_MÁY'] == search_query].sort_values('NGAY_FIX', ascending=False)
    if not history.empty:
        with st.expander(f"Hồ sơ máy {search_query}", expanded=True):
            c_a, c_b, c_c = st.columns(3)
            c_a.metric("Số lần sửa", f"{len(history)} lần")
            c_b.metric("Vùng", history['VÙNG_MIỀN'].iloc[0])
            c_c.warning("Tình trạng: Cần theo dõi" if len(history) >= 2 else "Tình trạng: Tốt")
            st.table(history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
    else:
        st.error("Không tìm thấy mã máy này.")

st.divider()

# 2. KPIs CHUYÊN SÂU
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Tổng lượt hỏng (Kỳ này)", f"{len(df_filtered):,}")
with k2:
    st.metric("Tài sản lỗi (Máy)", f"{df_filtered['MÃ_MÁY'].nunique():,}")
with k3:
    # Dự báo linh kiện cần chuẩn bị cho tháng sau
    next_month_est = int(len(df_filtered) / len(selected_months)) if selected_months else 0
    st.metric("Dự báo ca hỏng/tháng tới", next_month_est, delta="Dự trù kho")
with k4:
    # Tính tỷ lệ máy lỗi lặp lại
    repeat_rate = (df_filtered['MÃ_MÁY'].value_counts() >= 2).sum()
    st.metric("Máy lỗi lặp lại", repeat_rate, delta="Cần thanh lý", delta_color="inverse")

st.divider()

# 3. BIỂU ĐỒ PHÂN TÍCH
c_left, c_right = st.columns([1, 1])

with c_left:
    st.subheader("🛠️ Phân tích Linh kiện/Lý do hỏng (Top 15)")
    reasons = df_filtered['LÝ_DO_HỎNG'].value_counts().head(15).reset_index()
    fig_bar = px.bar(reasons, x='count', y='LÝ_DO_HỎNG', orientation='h', text_auto=True,
                     color='count', color_continuous_scale='Turbo')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with c_right:
    st.subheader("📈 Xu hướng phát sinh lỗi")
    trend = df_filtered.groupby('NGAY_FIX').size().reset_index()
    trend.columns = ['Ngày', 'Số ca']
    fig_trend = px.area(trend, x='Ngày', y='Số ca', line_shape='spline')
    st.plotly_chart(fig_trend, use_container_width=True)



# 4. DANH SÁCH "ĐEN" - CẢNH BÁO TÀI SẢN
st.subheader("🚨 Cảnh báo: Tài sản ngốn chi phí nhất (Hỏng >= 3 lần)")
bad_list = df_filtered['MÃ_MÁY'].value_counts()
bad_list = bad_list[bad_list >= 3].reset_index()
bad_list.columns = ['Mã Máy', 'Số lần hỏng trong kỳ']
st.dataframe(bad_list, use_container_width=True)

with st.expander("📋 Xem toàn bộ nhật ký kỳ này"):
    st.dataframe(df_filtered[['MÃ_MÁY', 'VÙNG_MIỀN', 'LÝ_DO_HỎNG', 'NGAY_FIX']].tail(100), use_container_width=True)
