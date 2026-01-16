import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Laptop Enterprise", layout="wide")

# Link dữ liệu chuẩn của sếp
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
        # Loại bỏ các dòng không có ngày để báo cáo thời gian chính xác
        df = df.dropna(subset=['NGAY_FIX']) 
        
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

# --- SIDEBAR: QUẢN TRỊ THỜI GIAN & KHU VỰC ---
with st.sidebar:
    st.header("🕒 Bộ lọc Chuyên gia")
    
    # Lọc Năm
    list_years = sorted(df['YEAR'].unique(), reverse=True)
    selected_year = st.selectbox("Chọn Năm báo cáo", list_years)
    
    # Lọc Tháng (Chỉ hiện tháng có trong năm đã chọn)
    df_year = df[df['YEAR'] == selected_year]
    list_months = sorted(df_year['MONTH'].unique())
    selected_months = st.multiselect("Chọn Tháng", options=list_months, default=list_months, format_func=lambda x: f"Tháng {x}")
    
    st.header("📍 Khu vực")
    list_vung = ["Miền Bắc", "Miền Trung", "Miền Nam"]
    selected_vung = st.multiselect("Chọn Vùng", list_vung, default=list_vung)
    
    st.divider()
    st.write(f"✅ Đang quét: **{len(df)}** dòng dữ liệu")

# LỌC DỮ LIỆU TỔNG
mask = (df['YEAR'] == selected_year) & (df['MONTH'].isin(selected_months)) & (df['VÙNG_MIỀN'].isin(selected_vung))
df_filtered = df[mask]

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Enterprise IT Asset Management Dashboard")

# 1. TRUY VẾT MÃ MÁY (Sửa lỗi Syntax tại đây)
st.markdown("### 🔍 Truy vết Hồ sơ bệnh án thiết bị")
search_query = st.text_input("Nhập chính xác mã máy (Ví dụ: 2498)", key="expert_search").strip()

if search_query:
    history = df[df['MÃ_MÁY'] == search_query].sort_values('NGAY_FIX', ascending=False)
    if not history.empty:
        with st.container(border=True):
            st.info(f"📋 **HỒ SƠ THIẾT BỊ: {search_query}**")
            c_a, c_b, c_c = st.columns(3)
            num_fixes = len(history)
            c_a.metric("Số lần sửa", f"{num_fixes} lần")
            c_b.metric("Vùng quản lý", history['VÙNG_MIỀN'].iloc[0])
            status = "🚨 NGUY CƠ CAO" if num_fixes >= 3 else "✅ BÌNH THƯỜNG"
            c_c.metric("Tình trạng", status)
            
            st.write("**Lịch sử chi tiết:**")
            st.table(history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
    else:
        st.error(f"Không tìm thấy mã máy '{search_query}'")

st.divider()

# 2. KPIs CHIẾN LƯỢC
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Tổng lượt hỏng (Kỳ này)", f"{len(df_filtered):,}")
with k2:
    st.metric("Số máy phát sinh lỗi", f"{df_filtered['MÃ_MÁY'].nunique():,}")
with k3:
    # Dự báo dựa trên trung bình các tháng đã chọn
    avg_per_month = len(df_filtered) / len(selected_months) if selected_months else 0
    st.metric("Dự báo ca lỗi/tháng tới", int(avg_per_month), delta="Linh kiện dự phòng")
with k4:
    repeat_count = (df_filtered['MÃ_MÁY'].value_counts() >= 3).sum()
    st.metric("Số máy cần thanh lý", repeat_count, delta="Lỗi >= 3 lần", delta_color="inverse")

st.divider()

# 3. BIỂU ĐỒ PHÂN TÍCH 
col_left, col_right = st.columns([6, 4])

with col_left:
    st.subheader("🛠️ Top 15 Lý do hỏng / Linh kiện (Cột D)")
    reasons = df_filtered['LÝ_DO_HỎNG'].value_counts().head(15).reset_index()
    reasons.columns = ['Lý do', 'Số lượng']
    fig_bar = px.bar(reasons, x='Số lượng', y='Lý do', orientation='h', text_auto=True,
                     color='Số lượng', color_continuous_scale='Turbo')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.subheader("📍 Tỷ lệ lỗi theo khu vực")
    vung_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
    fig_pie = px.pie(vung_data, values='count', names='VÙNG_MIỀN', hole=0.5,
