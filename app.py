import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# ID FILE CHUẨN (Dựa trên link Google Sheets mới nhất của sếp)
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
SHEET_NAME = "LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE"

URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=60)
def load_data():
    try:
        # Đọc dữ liệu với header dòng 2
        df = pd.read_csv(URL, header=1)
        # Làm sạch
        df = df.dropna(subset=["Mã số máy"])
        df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
        return df
    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🌐 Dashboard Quản trị Online")

if not df.empty:
    st.success("✅ Kết nối thành công!")
    st.metric("Tổng ca lỗi", len(df))
    st.dataframe(df, use_container_width=True)
else:
    st.info("💡 Sếp kiểm tra lại: 1. Đã tạo file app.py chưa? 2. Đã lưu file dạng Google Sheets chưa?")
