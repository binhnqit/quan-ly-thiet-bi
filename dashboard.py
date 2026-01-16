import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Laptop Toàn Quốc", layout="wide")

# Link CSV xuất bản đã thành công của sếp
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60) # Cập nhật mỗi phút
def load_final_data():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]

        # Áp dụng tọa độ chuẩn từ image_055f3d
        col_kv = "COL_3" # Cột Chi nhánh
        col_ma = "COL_1" # Cột Mã máy
        col_ngay = "COL_6" # Cột Ngày ghi nhận

        def fix_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df[col_kv].apply(fix_region)
        df['MÃ_MÁY_FIX'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Xử lý ngày tháng để làm biểu đồ xu hướng
        df['NGAY_DATETIME'] = pd.to_datetime(df[col_ngay], errors='coerce', dayfirst=True)
        
        # Lọc bỏ dòng tiêu đề thừa
        df = df[df['MÃ_MÁY_FIX'] != 'nan']
        df = df[~df['MÃ_MÁY_FIX'].str.contains("STT|MÃ|THEO", na=False)]
        
        return df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame()

df = load_final_data()

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Dashboard Quản trị Thiết bị Toàn Quốc")

if not df.empty:
    # 1. BỘ LỌC SIDEBAR
    with st.sidebar:
        st.header("📍 Bộ lọc dữ liệu")
        all_regions = ["Miền Bắc", "Miền Trung", "Miền Nam", "Khác/Chưa nhập"]
        selected_regions = st.multiselect("Chọn vùng miền hiển thị", all_regions, default=all_regions)
        
    df_filtered = df[df['VÙNG_MIỀN'].isin(selected_regions)]

    # 2. CHỈ SỐ KPI CHÍNH
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy hỏng khác nhau", df_filtered['MÃ_MÁY_FIX'].nunique())
    
    # Tính số ca Miền Nam riêng biệt
    mn_count = len(df[df['VÙNG_MIỀN'] == "Miền Nam"])
    c3.metric("Số ca Miền Nam", mn_count, delta=f"Dòng cuối: {len(df)}")
    
    # Tính tỷ lệ máy lỗi lặp lại
    repeat_rate = (df_filtered['MÃ_MÁY_FIX'].value_counts() > 1).sum()
    c4.metric("Máy lỗi >1 lần", repeat_rate)

    st.divider()

    # 3. BIỂU ĐỒ PHÂN TÍCH
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📊 Phân bổ lỗi theo Vùng")
        chart_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
        chart_data.columns = ['Vùng', 'Số lượng']
        fig_bar = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                         color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("📈 Xu hướng lỗi theo thời gian")
        trend_data = df_filtered.dropna(subset=['NGAY_DATETIME']).groupby(df_filtered['NGAY_DATETIME'].dt.date).size().reset_index()
        trend_data.columns = ['Ngày', 'Số lượng']
        fig_line = px.line(trend_data, x='Ngày', y='Số lượng', markers=True)
        fig_line.update_traces(line_color='#FF4B4B')
        st.plotly_chart(fig_line, use_container_width=True)

    # 4. DANH SÁCH CHI TIẾT
    st.subheader("📋 Danh sách thiết bị (Top 50 dòng mới nhất)")
    # Hiển thị các cột quan trọng nhất cho sếp dễ nhìn
    display_cols = ['COL_0', 'MÃ_MÁY_FIX', 'VÙNG_MIỀN', 'COL_4', 'COL_6']
    st.dataframe(df_filtered[display_cols].tail(50), use_container_width=True)

    # 5. NÚT XUẤT DỮ LIỆU
    st.sidebar.download_button(
        label="📥 Tải dữ liệu lọc (.csv)",
        data=df_filtered.to_csv(index=False).encode('utf-8-sig'),
        file_name='bao_cao_laptop.csv',
        mime='text/csv'
    )
else:
    st.warning("Đang tải dữ liệu, sếp chờ xíu nhé...")
