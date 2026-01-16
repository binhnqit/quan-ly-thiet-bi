import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# ID FILE MỚI NHẤT CỦA SẾP
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
SHEET_NAME = "LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE"

# Link xuất CSV (Google yêu cầu file phải được Share "Anyone with link")
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=60)
def load_data_cloud():
    try:
        # Đọc dữ liệu
        df = pd.read_csv(URL, header=1)
        
        # Làm sạch
        df = df.dropna(subset=["Mã số máy"])
        df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
        
        # Xử lý số liệu
        for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        return df
    except Exception as e:
        # Nếu vẫn lỗi 401, thông báo cho sếp biết
        if "401" in str(e):
            st.error("🔒 Lỗi 401: Sếp chưa 'Mở khóa' file. Hãy nhấn nút Share trên Google Sheets và chọn 'Anyone with link' nhé!")
        else:
            st.error(f"❌ Lỗi: {e}")
        return pd.DataFrame()

df = load_data_cloud()

# --- GIAO DIỆN ---
st.title("🛡️ Dashboard Quản lý Thiết bị Online")

if not df.empty:
    st.success("✅ Đã kết nối dữ liệu thành công!")
    # Hiển thị các chỉ số
    m1, m2 = st.columns(2)
    m1.metric("Tổng lượt báo lỗi", len(df))
    m2.metric("Tổng chi phí sửa chữa", f"{df['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    st.dataframe(df, use_container_width=True)
else:
    st.info("💡 Hệ thống đang chờ sếp cấp quyền 'Anyone with link' trên Google Sheets.")
