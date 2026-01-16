import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Quản lý Laptop Pro", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Dùng link export cơ bản nhất để tránh lỗi định dạng của Google
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=2)
def load_data_final_v4():
    try:
        # Đọc dữ liệu thô từ dòng 2 (Bỏ dòng tiêu đề to nhất)
        df = pd.read_csv(URL, header=1)
        
        # Xóa các dòng hoàn toàn trống và các cột không có tên
        df = df.dropna(how='all').loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Chuẩn hóa tên cột: Viết hoa, xóa khoảng trắng thừa
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # 🎯 TÌM CỘT BẰNG TỪ KHÓA (Rất quan trọng)
        # Tìm cột chứa chữ "CHI NHÁNH" hoặc "KHU VỰC"
        col_kv = next((c for c in df.columns if "CHI NHÁNH" in c or "KHU VỰC" in c), None)
        # Tìm cột chứa chữ "MÁY"
        col_ma = next((c for c in df.columns if "MÁY" in c), None)
        
        if col_kv and col_ma:
            # Lấy dữ liệu và dọn dẹp
            df = df.dropna(subset=[col_ma])
            
            def standardize(val):
                v = str(val).strip().upper()
                if "NAM" in v or v == "MN": return "Miền Nam"
                if "BẮC" in v or v == "MB": return "Miền Bắc"
                if any(x in v for x in ["TRUNG", "ĐN", "DN", "ĐÀ NẴNG"]): return "Miền Trung"
                return "Khác"

            df['Khu Vực'] = df[col_kv].apply(standardize)
            df['Mã máy'] = df[col_ma].astype(str).str.split('.').str[0]
            
            return df, col_kv
        return pd.DataFrame(), "Không tìm thấy cột Chi Nhánh"
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

df, col_found = load_data_final_v4()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar lọc
    regions = sorted(df['Khu Vực'].unique())
    selected = st.sidebar.multiselect("📍 Chọn Miền", regions, default=regions)
    df_filtered = df[df['Khu Vực'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy hỏng", df_filtered['Mã máy'].nunique())
    
    count_mn = len(df[df['Khu Vực'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", count_mn)

    st.divider()

    # Biểu đồ
    chart_data = df_filtered['Khu Vực'].value_counts().reset_index()
    chart_data.columns = ['Vùng', 'Số lượng']
    fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    # Bảng soi lỗi cho sếp
    with st.expander("🔍 Chi tiết dữ liệu"):
        st.write(f"App đang đọc cột: **{col_found}**")
        st.dataframe(df[['Mã máy', 'Khu Vực']].tail(20), use_container_width=True)
else:
    st.info("Sếp kiểm tra lại cột 'Chi Nhánh' trong file Sheets xem có đúng tên không nhé!")
