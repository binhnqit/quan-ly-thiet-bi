import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CẤU HÌNH WEB ---
st.set_page_config(page_title="Hệ thống Quản trị Laptop Cloud", layout="wide")

# Link Google Sheets của sếp (đã chuyển sang dạng export CSV để đọc nhanh)
SHEET_ID = "1GaWsUJutV4wixR3RUBZSTIMrgaD8fOIi"
SHEET_NAME = "LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE" # Tên sheet đã mã hóa URL
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=300) # Cập nhật dữ liệu mới mỗi 5 phút
def load_data_from_cloud():
    try:
        # Đọc dữ liệu từ Google Sheets công khai
        df = pd.read_csv(URL, header=1)
        
        # Làm sạch dữ liệu
        df = df.dropna(subset=["Mã số máy"])
        df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
        df["Ngày Xác nhận"] = pd.to_datetime(df["Ngày Xác nhận"], errors='coerce')
        
        # Xử lý chi phí
        for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        return df
    except Exception as e:
        st.error(f"⚠️ Không thể kết nối dữ liệu Cloud: {e}")
        return pd.DataFrame()

df = load_data_from_cloud()

# --- GIAO DIỆN CHÍNH (Giữ nguyên logic chuyên gia của chúng ta) ---
st.title("🌐 Hệ thống Quản lý Thiết bị Online")
st.info("Dữ liệu đang được kết nối trực tiếp với Google Drive của sếp.")

if not df.empty:
    # 1. Sidebar Lọc
    st.sidebar.header("Bộ lọc")
    mien = st.sidebar.multiselect("Chọn Miền", options=df["Chi Nhánh"].unique(), default=df["Chi Nhánh"].unique())
    df_filtered = df[df["Chi Nhánh"].isin(mien)]

    # 2. Metrics tài chính
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Tổng chi phí thực tế", f"{df_filtered['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    # 3. Phân tích máy hỏng nhiều (Thanh lý)
    st.subheader("🚨 Danh sách máy hỏng lặp lại (Cần thanh lý)")
    counts = df_filtered["Mã số máy"].value_counts()
    blacklist = counts[counts >= 2].index
    if not blacklist.empty:
        df_blacklist = df_filtered[df_filtered["Mã số máy"].isin(blacklist)]
        st.dataframe(df_blacklist, use_container_width=True)
    else:
        st.success("Chưa phát hiện máy nào hỏng lặp lại trong kỳ này.")

    # 4. Biểu đồ
    col_a, col_b = st.columns(2)
    with col_a:
        fig_mien = px.bar(df_filtered["Chi Nhánh"].value_counts().reset_index(), x='Chi Nhánh', y='count', title="Lỗi theo Miền")
        st.plotly_chart(fig_mien, use_container_width=True)
    with col_b:
        fig_loi = px.pie(df_filtered["Lý Do"].value_counts().reset_index(), values='count', names='Lý Do', title="Cơ cấu loại lỗi", hole=0.4)
        st.plotly_chart(fig_loi, use_container_width=True)

else:
    st.warning("Đang đợi dữ liệu từ Google Sheets...")
