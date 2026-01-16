import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link ID lấy trực tiếp từ hình của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Dùng link export cơ bản nhất để tránh lỗi 400 Bad Request
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def load_data_stable():
    try:
        # Đọc dữ liệu từ Google Sheets
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột (Xóa khoảng trắng)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Kiểm tra cột Masomay (tên mới sếp vừa đặt)
        if "Masomay" in df.columns:
            df = df.dropna(subset=["Masomay"])
            # Chuẩn hóa mã máy
            df["Masomay"] = df["Masomay"].astype(str).str.split('.').str[0]
            return df
        else:
            # Nếu không tìm thấy Masomay, hiển thị các cột đang có để sếp biết
            st.warning(f"Cột tìm thấy: {list(df.columns)}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {e}")
        return pd.DataFrame()

df = load_data_stable()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success("✅ Kết nối thành công!")
    
    # Dashboard số liệu
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt báo lỗi", len(df))
    
    # Biểu đồ Chi nhánh (Cột F trong hình của sếp)
    if "Chi Nhánh" in df.columns:
        st.subheader("🌎 Thống kê theo Chi nhánh")
        fig = px.bar(df["Chi Nhánh"].value_counts().reset_index(), 
                     x='index', y='Chi Nhánh', text_auto=True,
                     labels={'index': 'Chi nhánh', 'Chi Nhánh': 'Số ca'})
        st.plotly_chart(fig, use_container_width=True)

    # Hiển thị bảng dữ liệu chính
    st.subheader("📋 Chi tiết nhật ký thiết bị")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Sếp hãy kiểm tra lại quyền chia sẻ file Google Sheets nhé.")
    if st.button('Tải lại dữ liệu'):
        st.rerun()
