import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Đọc trực tiếp định dạng thô nhất để tránh lỗi định dạng của Google
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=1) # Tốc độ cập nhật cực nhanh
def load_data_v5_final():
    try:
        # Đọc dữ liệu từ dòng chứa tiêu đề
        df = pd.read_csv(URL, header=1)
        
        # 1. Dọn dẹp tên cột
        df.columns = [str(c).strip().upper() for c in df.columns]

        # 2. Tìm đúng cột "Chi Nhánh" (Cột F)
        col_kv = next((c for c in df.columns if any(k in c for k in ["CHI NHÁNH", "KHU VỰC", "CHI NHANH"])), df.columns[5])
        col_ma = next((c for c in df.columns if "MÁY" in c or "MASOMAY" in c), df.columns[1])

        # 3. Thuật toán nhận diện Miền Nam thông minh
        def super_detect(val):
            v = str(val).strip().upper()
            # Nếu sếp tô màu xanh mà chưa có chữ, hoặc có mã ẩn, ta quét theo từ khóa
            if any(x in v for x in ["NAM", "MN", "SOUTH"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB", "NORTH"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN", "CENTER"]): return "Miền Trung"
            return "Chưa phân loại"

        df['Khu Vực'] = df[col_kv].apply(super_detect)
        df['Mã máy'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Lọc bỏ các dòng không có mã máy (dòng trống)
        df = df[df['Mã máy'] != 'nan']
        
        return df, col_kv
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame(), None

df, found_col = load_data_v5_final()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar lọc
    vung_list = ["Miền Bắc", "Miền Trung", "Miền Nam", "Chưa phân loại"]
    selected = st.sidebar.multiselect("📍 Chọn Miền", vung_list, default=[v for v in vung_list if v in df['Khu Vực'].unique()])
    
    df_filtered = df[df['Khu Vực'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy khác nhau", df_filtered['Mã máy'].nunique())
    
    # Kiểm đếm riêng Miền Nam
    val_mn = len(df[df['Khu Vực'] == 'Miền Nam'])
    c3.metric("Dữ liệu Miền Nam", val_mn, delta="Đã nhận diện" if val_mn > 0 else "Kiểm tra ô màu xanh!")

    st.divider()

    # Biểu đồ
    chart_df = df_filtered['Khu Vực'].value_counts().reset_index()
    chart_df.columns = ['Vùng', 'Số ca']
    fig = px.bar(chart_df, x='Vùng', y='Số ca', color='Vùng', text_auto=True,
                 color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745", "Chưa phân loại": "#6c757d"})
    st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM TRA CHO SẾP (Quan trọng nhất)
    with st.expander("🔍 Soi dữ liệu thô (Dành cho sếp)"):
        st.write(f"Đang đọc dữ liệu từ cột: **{found_col}**")
        st.write("Dưới đây là 30 dòng mà App đang liệt vào nhóm 'Chưa phân loại'. Sếp xem chúng có chữ gì nhé:")
        df_khac = df[df['Khu Vực'] == 'Chưa phân loại'].tail(30)
        st.dataframe(df_khac[[found_col, 'Khu Vực']])

else:
    st.info("Sếp kiểm tra lại cột 'Chi Nhánh' trong file Sheets nhé!")
