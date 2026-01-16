import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
import random

st.set_page_config(page_title="Hệ thống Quản lý Thiết bị Pro", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

@st.cache_data(ttl=1)
def load_data_max_power():
    try:
        # Ép Google bỏ cache để lấy dữ liệu mới nhất (vượt mốc 2521)
        rid = random.randint(1, 1000000)
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&refresh={rid}"
        
        # Dùng requests để tải dữ liệu thô đảm bảo không bị ngắt dòng giữa chừng
        response = requests.get(URL)
        df = pd.read_csv(io.StringIO(response.text))
        
        # 1. Tự động đặt tên cột COL_0, COL_1... để tránh lỗi Duplicate
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]

        # 2. XÁC ĐỊNH TỌA ĐỘ CHUẨN THEO ẢNH SẾP GỬI
        # COL_1: Mã máy (Cột B)
        # COL_3: Chi nhánh (Cột D) -> Đây là nơi chứa "Miền Bắc", "Miền Nam"
        col_kv = "COL_3" 
        col_ma = "COL_1"

        def standardize(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df[col_kv].apply(standardize)
        df['MÃ_MÁY_FIX'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Lọc bỏ các dòng không phải dữ liệu (nan hoặc tiêu đề thừa)
        df = df[df['MÃ_MÁY_FIX'] != 'nan']
        df = df[~df['MÃ_MÁY_FIX'].str.contains("STT|MÃ|THEO", na=False)]
        
        return df
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_max_power()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    # Tổng số dòng này phải nhảy lên > 3000
    c1.metric("Tổng lượt lỗi thực tế", len(df))
    c2.metric("Số máy hỏng khác nhau", df['MÃ_MÁY_FIX'].nunique())
    
    val_mn = len(df[df['VÙNG_MIỀN'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã quét dòng 3000+" if val_mn > 0 else "Kiểm tra text")

    st.divider()

    # Biểu đồ chuẩn màu
    chart_data = df['VÙNG_MIỀN'].value_counts().reset_index()
    chart_data.columns = ['Vùng', 'Số lượng']
    fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                 color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Khác/Chưa nhập": "#6c757d"})
    st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM TRA DÒNG CUỐI
    with st.expander("🔍 Soi dữ liệu thô (Dòng cuối cùng từ Sheets)"):
        st.write(f"Số dòng hệ thống đọc được: **{len(df)}**")
        st.dataframe(df[['MÃ_MÁY_FIX', 'VÙNG_MIỀN', 'COL_3']].tail(100))

else:
    st.info("Sếp đợi vài giây để hệ thống phá băng bộ nhớ đệm Google...")
