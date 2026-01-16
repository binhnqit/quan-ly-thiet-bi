import streamlit as st
import pandas as pd
import plotly.express as px
import random

st.set_page_config(page_title="Hệ thống Quản trị Laptop Pro", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

@st.cache_data(ttl=1)
def load_data_force_range():
    try:
        rid = random.randint(1, 1000000)
        # THAY ĐỔI QUAN TRỌNG: Thêm tham số range=A1:Z5000 để ép quét qua dòng 2521
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&range=A1:Z5000&refresh={rid}"
        
        df = pd.read_csv(URL)
        
        # Đặt tên cột COL_0, COL_1... để an toàn tuyệt đối
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]

        # TỌA ĐỘ THEO DỮ LIỆU THỰC TẾ: Cột B (1) là Mã máy, Cột D (3) là Chi nhánh
        col_kv = "COL_3" 
        col_ma = "COL_1"

        def fix_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_HIỆN_THỊ'] = df[col_kv].apply(fix_region)
        df['MÃ_MÁY_FIX'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Lọc dòng trống
        df = df[df['MÃ_MÁY_FIX'] != 'nan']
        df = df[~df['MÃ_MÁY_FIX'].str.contains("STT|MÃ|THEO", na=False)]
        
        return df
    except Exception as e:
        st.error(f"Đang đồng bộ... ({e})")
        return pd.DataFrame()

df = load_data_force_range()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    # Hy vọng con số này sẽ nhảy lên 3647
    c1.metric("Tổng lượt lỗi thực tế", len(df))
    c2.metric("Số máy hỏng khác nhau", df['MÃ_MÁY_FIX'].nunique())
    
    val_mn = len(df[df['VÙNG_HIỆN_THỊ'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Dòng 3000+" if val_mn > 0 else None)

    st.divider()

    # Biểu đồ theo màu nhận diện thương hiệu
    chart_data = df['VÙNG_HIỆN_THỊ'].value_counts().reset_index()
    chart_data.columns = ['Vùng', 'Số lượng']
    fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                 color_discrete_map={
                     "Miền Bắc": "#007bff", 
                     "Miền Trung": "#ffc107", 
                     "Miền Nam": "#28a745", 
                     "Khác/Chưa nhập": "#6c757d"
                 })
    st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM TRA MẤU CHỐT
    with st.expander("🔍 Kiểm tra mốc dữ liệu 3647"):
        st.write(f"Số dòng hệ thống vừa quét được: **{len(df)}**")
        st.dataframe(df.tail(100))

else:
    st.info("Sếp vui lòng chờ trong giây lát...")
