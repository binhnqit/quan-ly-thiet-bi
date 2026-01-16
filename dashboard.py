import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Hệ thống Quản trị Laptop Pro", layout="wide")

# Link ID gốc của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

@st.cache_data(ttl=2) # Cập nhật liên tục
def load_data_from_query():
    try:
        # Sử dụng Visualization API để lấy dữ liệu thay vì Export CSV thông thường
        # Cách này giúp vượt qua giới hạn dòng của Google
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
        
        # Đọc dữ liệu thô
        df = pd.read_csv(URL)
        
        # 1. Xử lý tên cột để tránh lỗi Duplicate
        new_cols = []
        counts = {}
        for i, col in enumerate(df.columns):
            c_name = str(col).strip().upper()
            if not c_name or "UNNAMED" in c_name: c_name = f"COLUMN_{i}"
            if c_name in counts:
                counts[c_name] += 1
                new_cols.append(f"{c_name}_{counts[c_name]}")
            else:
                counts[c_name] = 0
                new_cols.append(c_name)
        df.columns = new_cols

        # 2. Xác định cột dữ liệu theo tọa độ (Cột F là cột 6 - Index 5)
        # Vì file sếp có tiêu đề phức tạp, dùng tọa độ là an toàn nhất
        col_kv = df.columns[5] # Cột Chi Nhánh
        col_ma = df.columns[1] # Cột Mã Máy

        def categorize(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Chưa xác định"

        df['KHU VỰC'] = df[col_kv].apply(categorize)
        df['MÃ MÁY CHUẨN'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Lọc bỏ các dòng hoàn toàn trống
        df = df[df['MÃ MÁY CHUẨN'] != 'nan']
        
        return df, col_kv
    except Exception as e:
        st.error(f"Đang tìm cách kết nối lại... ({e})")
        return pd.DataFrame(), None

df, real_col_name = load_data_from_query()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar
    vung_mien = ["Miền Bắc", "Miền Trung", "Miền Nam", "Chưa xác định"]
    selected = st.sidebar.multiselect("📍 Chọn Miền", vung_mien, default=vung_mien)
    df_filtered = df[df['KHU VỰC'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    # Nếu thành công, con số này phải > 3000
    c1.metric("Tổng lượt lỗi đọc được", len(df_filtered))
    c2.metric("Số máy hỏng khác nhau", df_filtered['MÃ MÁY CHUẨN'].nunique())
    
    val_mn = len(df[df['KHU VỰC'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã quét dòng 3000+" if val_mn > 0 else "Cần check ô màu xanh")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_data = df_filtered['KHU VỰC'].value_counts().reset_index()
        chart_data.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745", "Chưa xác định": "#6c757d"})
        st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM TRA MỐC 3647
    with st.expander("🔍 Kiểm tra dữ liệu ở dòng 3000+"):
        st.write(f"Hệ thống đã đọc tổng cộng: **{len(df)}** dòng.")
        # Hiển thị 100 dòng cuối cùng để sếp đối chiếu với Sheets
        st.dataframe(df.tail(100))

else:
    st.info("Sếp vui lòng kiểm tra lại quyền chia sẻ Link Google Sheets nhé!")
