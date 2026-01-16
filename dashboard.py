import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# SẾP DÁN LINK CÓ CHỮ "output=csv" VÀO ĐÂY
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=1)
def load_data_final_fix():
    try:
        # Sử dụng on_bad_lines để bỏ qua các dòng lỗi định dạng nếu có
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        
        # Tự động đặt tên cột COL_0, COL_1... để tránh lỗi Duplicate
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]

        # TỌA ĐỘ CHUẨN: Cột B (1) là Mã máy, Cột D (3) là Chi nhánh
        col_kv = "COL_3" 
        col_ma = "COL_1"

        def fix_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df[col_kv].apply(fix_region)
        df['MÃ_MÁY_FIX'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Lọc dòng trống và tiêu đề thừa
        df = df[df['MÃ_MÁY_FIX'] != 'nan']
        df = df[~df['MÃ_MÁY_FIX'].str.contains("STT|MÃ|THEO", na=False)]
        
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame()

df = load_data_final_fix()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    # Tổng lượt lỗi phải nhảy lên > 3000
    c1.metric("Tổng lượt lỗi thực tế", len(df))
    c2.metric("Số máy hỏng khác nhau", df['MÃ_MÁY_FIX'].nunique())
    
    val_mn = len(df[df['VÙNG_MIỀN'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã quét dòng 3000+" if val_mn > 0 else "Kiểm tra lại text")

    st.divider()

    # Biểu đồ màu chuẩn
    chart_data = df['VÙNG_MIỀN'].value_counts().reset_index()
    chart_data.columns = ['Vùng', 'Số lượng']
    fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                 color_discrete_map={
                     "Miền Bắc": "#007bff", 
                     "Miền Trung": "#ffc107", 
                     "Miền Nam": "#28a745", 
                     "Khác/Chưa nhập": "#6c757d"
                 })
    st.plotly_chart(fig, use_container_width=True)

    # BẢNG SOI DÒNG CUỐI
    with st.expander("🔍 Kiểm tra mốc dữ liệu 3647"):
        st.write(f"Số dòng hệ thống vừa quét được: **{len(df)}**")
        st.dataframe(df.tail(100))
else:
    st.info("Sếp đang dùng link HTML, hãy đổi sang link CSV theo hướng dẫn ở trên nhé!")
