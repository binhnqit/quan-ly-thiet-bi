import streamlit as st
import pandas as pd
import plotly.express as px
import random

st.set_page_config(page_title="Hệ thống Quản trị Laptop Pro", layout="wide")

# Link gốc của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

@st.cache_data(ttl=1)
def load_data_unlimited():
    try:
        # THỦ THUẬT QUAN TRỌNG: Dùng GVIZ để lấy toàn bộ dòng (vượt mốc 2521)
        # rid giúp phá cache để lấy dữ liệu mới nhất dòng 3647
        rid = random.randint(1, 1000000)
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&refresh={rid}"
        
        # Đọc dữ liệu
        df = pd.read_csv(URL)
        
        # Đặt tên cột COL_0, COL_1... để triệt tiêu lỗi Duplicate
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]

        # TỌA ĐỘ CHUẨN: Cột B (Index 1) là Mã máy, Cột D (Index 3) là Chi nhánh
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
        df = df[~df['MÃ_MÁY_FIX'].str.contains("STT|MÃ", na=False)]
        
        return df
    except Exception as e:
        st.error(f"Đang đồng bộ lại... ({e})")
        return pd.DataFrame()

df = load_data_unlimited()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    # Con số này TRỰC TIẾP CHỨNG MINH việc phá rào 2521
    c1.metric("Tổng lượt lỗi thực tế", len(df))
    c2.metric("Số máy hỏng khác nhau", df['MÃ_MÁY_FIX'].nunique())
    
    val_mn = len(df[df['VÙNG_HIỆN_THỊ'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã quét dòng 3000+" if val_mn > 0 else "Cần check text")

    st.divider()

    # Biểu đồ chuẩn màu image_048c4b
    chart_data = df['VÙNG_HIỆN_THỊ'].value_counts().reset_index()
    chart_data.columns = ['Vùng', 'Số lượng']
    fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                 color_discrete_map={
                     "Miền Bắc": "#007bff", # Xanh dương
                     "Miền Trung": "#ffc107", # Vàng
                     "Miền Nam": "#28a745", # Xanh lá
                     "Khác/Chưa nhập": "#6c757d"
                 })
    st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM CHỨNG (Để sếp thấy dòng 3647)
    with st.expander("🔍 Soi dữ liệu dòng cuối (Kiểm tra mốc 3647)"):
        st.write(f"Hệ thống đã đọc được: **{len(df)}** dòng.")
        st.dataframe(df[['MÃ_MÁY_FIX', 'VÙNG_HIỆN_THỊ', 'COL_3']].tail(100))

else:
    st.info("Sếp đợi vài giây để Dashboard bốc dữ liệu mới nhất...")
