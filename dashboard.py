import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link ID từ hình của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Dùng link này để Google ép xuất dữ liệu mới nhất
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0&refresh={time.time()}"

def load_data_ultra():
    try:
        # Đọc dữ liệu thô, không quan tâm tiêu đề là gì
        df = pd.read_csv(URL)
        
        # ÉP TÊN CỘT MỚI (Dựa theo thứ tự hình image_f93aaa.png của sếp)
        # Cách này giúp app không bao giờ bị báo "Không tìm thấy cột"
        new_columns = ['STT', 'Ma_So_May', 'Ten_KH', 'Ly_Do', 'Du_Doan', 'Chi_Nhanh', 'Ngay', 'Nguoi_Kiem', 'Phi_Du_Kien', 'Phi_Thuc_Te']
        
        # Chỉ lấy số lượng cột tương ứng để tránh lỗi nếu sếp thêm cột
        df.columns = new_columns[:len(df.columns)]
        
        # Làm sạch: Loại bỏ dòng tiêu đề nếu bị lặp lại và dòng trống
        df = df[df['Ma_So_May'].notna()]
        df = df[df['Ma_So_May'] != 'Mã số máy']
        
        # Chuẩn hóa mã máy
        df['Ma_So_May'] = df['Ma_So_May'].astype(str).str.split('.').str[0].str.strip()
        
        # Chuyển chi phí sang số
        df['Phi_Thuc_Te'] = pd.to_numeric(df['Phi_Thuc_Te'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Đang kết nối lại với máy chủ Google... (Lỗi: {e})")
        return pd.DataFrame()

df = load_data_ultra()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success("✅ ĐÃ KẾT NỐI TRỰC TIẾP THÀNH CÔNG!")
    
    # Chỉ số Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng lượt lỗi", len(df))
    m2.metric("Tổng chi phí", f"{df['Phi_Thuc_Te'].sum():,.0f} VNĐ")
    
    counts = df['Ma_So_May'].value_counts()
    m3.metric("Máy hỏng ≥ 2 lần", len(counts[counts >= 2]))

    st.divider()

    # Biểu đồ và Bảng
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("🌎 Lỗi theo Chi nhánh")
        fig = px.bar(df['Chi_Nhanh'].value_counts().reset_index(), x='index', y='Chi_Nhanh', text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("📋 Danh sách dữ liệu")
        st.dataframe(df, use_container_width=True)
else:
    st.info("Sếp đợi vài giây để dữ liệu từ Google Sheets đổ về Dashboard...")
    if st.button('Ép tải lại ngay'):
        st.rerun()
