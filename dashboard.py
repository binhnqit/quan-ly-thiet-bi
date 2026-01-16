import streamlit as st
import pandas as pd
import plotly.express as px
import random

st.set_page_config(page_title="Hệ thống Quản lý Thiết bị Toàn Quốc", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

@st.cache_data(ttl=1) # Cập nhật mỗi giây
def load_data_unlimited():
    try:
        # Tạo số ngẫu nhiên để đánh lừa bộ nhớ đệm của Google
        rid = random.randint(1, 1000000)
        # Sử dụng link export thô nhất nhưng ép xóa cache
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&refresh={rid}"
        
        # Đọc dữ liệu (Bỏ qua 2 dòng tiêu đề gộp ô của sếp)
        df = pd.read_csv(URL, skiprows=2)
        
        # Dọn dẹp tên cột trùng lặp (tránh lỗi Duplicate Column)
        new_cols = []
        counts = {}
        for col in df.columns:
            c = str(col).strip().upper()
            if c in counts:
                counts[c] += 1
                new_cols.append(f"{c}_{counts[c]}")
            else:
                counts[c] = 0
                new_cols.append(c)
        df.columns = new_cols

        # Bốc dữ liệu tại Cột F (Index 5) và Cột B (Index 1)
        col_kv = df.columns[5] if len(df.columns) > 5 else df.columns[0]
        col_ma = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        def fix_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['Vùng'] = df[col_kv].apply(fix_region)
        df['Mã số'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Loại bỏ dòng trắng
        df = df[df['Mã số'] != 'nan']
        
        return df
    except Exception as e:
        st.error(f"Lỗi đồng bộ: {e}")
        return pd.DataFrame()

df = load_data_unlimited()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    # CON SỐ NÀY PHẢI NHẢY LÊN ~3600
    c1.metric("Tổng số dòng đọc được", len(df))
    c2.metric("Số máy khác nhau", df['Mã số'].nunique())
    
    val_mn = len(df[df['Vùng'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn)

    st.divider()

    # Biểu đồ
    chart_data = df['Vùng'].value_counts().reset_index()
    chart_data.columns = ['Vùng', 'Số lượng']
    fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                 color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
    st.plotly_chart(fig, use_container_width=True)

    # BẢNG SOI DÒNG CUỐI (Để sếp đối chiếu dòng 3647)
    with st.expander("🔍 Kiểm tra 100 dòng cuối cùng từ Sheets"):
        st.write("Nếu sếp thấy dữ liệu Miền Nam ở đây mà biểu đồ không hiện, báo tôi ngay!")
        st.dataframe(df.tail(100))

else:
    st.info("Đang kết nối lại...")
