import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# ID file chuẩn từ hình 7 của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

# Kỹ thuật phá cache bằng mốc thời gian thực
now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
# Sử dụng link công khai dạng tsv (tab-separated values) đôi khi ổn định hơn csv khi bị kẹt cache
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&cache_buster={now}"

@st.cache_data(ttl=5)
def load_data_final():
    try:
        # Đọc dữ liệu (header=0 vì sếp đã đưa tiêu đề lên dòng 1 ở hình image_f93aaa.png)
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        if "Mã số máy" in df.columns:
            df = df.dropna(subset=["Mã số máy"])
            # Chuyển mã máy về dạng chuỗi chuẩn, loại bỏ phần thập phân
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.split('.').str[0]
            
            # Chuyển đổi chi phí sang số
            for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# Tải dữ liệu
df = load_data_final()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success(f"✅ Đã kết nối thành công! Hệ thống tìm thấy {len(df)} bản ghi.")
    
    # Chỉ số nhanh
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df))
    total_spent = df["Chi Phí Thực Tế"].sum() if "Chi Phí Thực Tế" in df.columns else 0
    c2.metric("Tổng chi phí", f"{total_spent:,.0f} VNĐ")
    
    # Máy hỏng lặp lại
    counts = df["Mã số máy"].value_counts()
    blacklist = counts[counts >= 2]
    c3.metric("Máy cần thanh lý", len(blacklist))

    st.divider()
    
    # Biểu đồ và bảng dữ liệu
    col1, col2 = st.columns([1, 1])
    with col1:
        if "Chi Nhánh" in df.columns:
            fig = px.bar(df["Chi Nhánh"].value_counts().reset_index(), x='index', y='Chi Nhánh', title="Lỗi theo Chi nhánh")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("📋 Danh sách chi tiết")
        st.dataframe(df, use_container_width=True)
else:
    st.error("🚨 App vẫn chưa thấy dữ liệu cũ từ bộ nhớ.")
    st.info("Sếp hãy thử: Mở trình duyệt ở chế độ Ẩn danh (Ctrl+Shift+N) để truy cập link app xem sao nhé!")
    if st.button('🔄 Cố gắng tải lại lần nữa'):
        st.cache_data.clear()
        st.rerun()
