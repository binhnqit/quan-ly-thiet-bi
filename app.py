import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Thiết lập trang
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# 2. Link xuất dữ liệu trực tiếp (Đã tối ưu cho cấu hình hình 7 của sếp)
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Hàm tải dữ liệu không sử dụng cache cũ nếu bị lỗi
def load_data_fresh():
    try:
        # Đọc trực tiếp vì sếp đã để tiêu đề ở dòng 1
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        if "Mã số máy" in df.columns:
            df = df.dropna(subset=["Mã số máy"])
            # Xử lý mã máy tránh hiện số thập phân .0
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.split('.').str[0]
            
            # Chuyển đổi chi phí
            for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {e}")
        return pd.DataFrame()

# Nút bấm cưỡng bức cập nhật ở Sidebar
if st.sidebar.button('🔄 LÀM MỚI TOÀN BỘ'):
    st.cache_data.clear()
    st.rerun()

df = load_data_fresh()

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success(f"✅ Tuyệt vời sếp ơi! Đã kết nối thành công {len(df)} dòng dữ liệu.")
    
    # Chỉ số Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df))
    c2.metric("Tổng chi phí thực tế", f"{df['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    counts = df["Mã số máy"].value_counts()
    blacklist = counts[counts >= 2]
    c3.metric("Máy hỏng ≥ 2 lần", len(blacklist), delta="Cần thanh lý", delta_color="inverse")

    # Biểu đồ
    st.divider()
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("🌎 Lỗi theo Chi nhánh")
        fig_branch = px.bar(df["Chi Nhánh"].value_counts().reset_index(), 
                            x='index', y='Chi Nhánh', color='index', text_auto=True)
        st.plotly_chart(fig_branch, use_container_width=True)
    with col_right:
        st.subheader("🧩 Cơ cấu loại hư hỏng")
        fig_reason = px.pie(df, names='Lý Do', hole=0.4)
        st.plotly_chart(fig_reason, use_container_width=True)

    # Danh sách máy hỏng nhiều
    if not blacklist.empty:
        st.subheader("🚨 Danh sách máy cần thanh lý")
        st.dataframe(df[df["Mã số máy"].isin(blacklist.index)].sort_values("Mã số máy"), use_container_width=True)

    with st.expander("🔍 Chi tiết dữ liệu thô"):
        st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ App chưa nhận được dữ liệu mới. Sếp hãy nhấn nút 'LÀM MỚI TOÀN BỘ' ở bên trái nhé!")
