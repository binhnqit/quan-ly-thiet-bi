import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. Cấu hình trang
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# 2. Link xuất dữ liệu (Dùng link export trực tiếp cho nhanh)
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

# THUẬT TOÁN PHÁ CACHE: Thêm thời gian hiện tại vào link để App luôn lấy dữ liệu mới nhất
t = time.time()
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&refresh={t}"

def load_data_final():
    try:
        # Đọc trực tiếp (Vì sếp đã đưa tiêu đề lên dòng 1 ở hình image_f93aaa.png)
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        # Kiểm tra cột "Mã số máy"
        if "Mã số máy" in df.columns:
            df = df.dropna(subset=["Mã số máy"])
            # Chuyển mã máy về dạng chuỗi chuẩn
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.split('.').str[0]
            
            # Chuyển đổi chi phí sang số
            for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối kỹ thuật: {e}")
        return pd.DataFrame()

# Tự động tải dữ liệu
df = load_data_final()

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success(f"✅ THÀNH CÔNG RỒI SẾP ƠI! Đã nhận được {len(df)} dòng dữ liệu.")
    
    # Chỉ số nhanh
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df))
    c2.metric("Tổng chi phí thực tế", f"{df.get('Chi Phí Thực Tế', pd.Series([0])).sum():,.0f} VNĐ")
    
    counts = df["Mã số máy"].value_counts()
    blacklist = counts[counts >= 2]
    c3.metric("Máy hỏng ≥ 2 lần", len(blacklist))

    # Biểu đồ
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if "Chi Nhánh" in df.columns:
            st.subheader("🌎 Lỗi theo Chi nhánh")
            fig = px.bar(df["Chi Nhánh"].value_counts().reset_index(), x='index', y='Chi Nhánh', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
    with col_b:
        if "Lý Do" in df.columns:
            st.subheader("🧩 Cơ cấu hư hỏng")
            fig_pie = px.pie(df, names='Lý Do', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # Hiển thị bảng dữ liệu
    st.subheader("📋 Chi tiết nhật ký")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("🔄 Đang ép bộ nhớ đệm tải lại dữ liệu... Sếp đợi 5 giây rồi nhấn F5 trình duyệt nhé!")
    if st.button('Bấm vào đây nếu vẫn chưa thấy dữ liệu'):
        st.rerun()
