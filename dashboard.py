import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# SẾP DÁN CÁI LINK VỪA COPY Ở BƯỚC 1 VÀO ĐÂY
# Nó sẽ có dạng: https://docs.google.com/spreadsheets/d/e/2PACX-.../pub?output=csv
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pubhtml?gid=675485241&single=true"

@st.cache_data(ttl=5)
def load_data_complete():
    try:
        # Link xuất bản (Publish) là cách mạnh nhất để lấy đủ 3647 dòng
        df = pd.read_csv(PUBLISHED_URL)
        
        # Tự động đặt tên cột để tránh lỗi Duplicate
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

df = load_data_complete()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    # Con số này PHẢI vượt qua 2521
    c1.metric("Tổng lượt lỗi thực tế", len(df))
    c2.metric("Số máy hỏng khác nhau", df['MÃ_MÁY_FIX'].nunique())
    
    val_mn = len(df[df['VÙNG_MIỀN'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn)

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

    # PHẦN KIỂM CHỨNG TỐI THƯỢNG
    with st.expander("🔍 Kiểm tra dòng cuối cùng (Mốc 3647)"):
        st.write(f"Hệ thống đã đọc được tổng cộng: **{len(df)}** dòng.")
        st.dataframe(df.tail(50))
else:
    st.info("Sếp vui lòng dán link 'Xuất bản lên web' vào code nhé!")
