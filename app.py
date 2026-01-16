import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Thiết lập trang
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# 2. Link xuất dữ liệu trực tiếp từ Google Sheets chuẩn của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Hàm tải dữ liệu tươi mới
def load_data_fresh():
    try:
        # Đọc trực tiếp vì sếp đã để tiêu đề ở dòng 1 cực chuẩn
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột (xóa khoảng trắng dư thừa)
        df.columns = [str(c).strip() for c in df.columns]
        
        if "Mã số máy" in df.columns:
            # Loại bỏ các dòng hoàn toàn trống
            df = df.dropna(subset=["Mã số máy"])
            
            # Xử lý mã máy tránh hiện số thập phân (như 355.0)
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.split('.').str[0]
            
            # Chuyển đổi các cột chi phí sang dạng số để tính toán
            for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {e}")
        return pd.DataFrame()

# Nút bấm cưỡng bức cập nhật ở thanh bên (Sidebar)
if st.sidebar.button('🔄 LÀM MỚI TOÀN BỘ'):
    st.cache_data.clear()
    st.rerun()

df = load_data_fresh()

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success(f"✅ Tuyệt vời sếp ơi! Đã kết nối thành công dữ liệu.")
    
    # Các chỉ số quan trọng
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt báo lỗi", len(df))
    
    total_cost = df["Chi Phí Thực Tế"].sum() if "Chi Phí Thực Tế" in df.columns else 0
    c2.metric("Tổng chi phí thực tế", f"{total_cost:,.0f} VNĐ")
    
    # Tìm máy hỏng nhiều lần (Blacklist)
    counts = df["Mã số máy"].value_counts()
    blacklist = counts[counts >= 2]
    c3.metric("Máy hỏng ≥ 2 lần", len(blacklist), delta="Cần thanh lý", delta_color="inverse")

    # Biểu đồ phân tích
    st.divider()
    col_left, col_right = st.columns(2)
    
    with col_left:
        if "Chi Nhánh" in df.columns:
            st.subheader("🌎 Lỗi theo Chi nhánh")
            fig_branch = px.bar(df["Chi Nhánh"].value_counts().reset_index(), 
                                x='index', y='Chi Nhánh', color='index', text_auto=True,
                                labels={'index': 'Chi nhánh', 'Chi Nhánh': 'Số ca lỗi'})
            st.plotly_chart(fig_branch, use_container_width=True)
            
    with col_right:
        if "Lý Do" in df.columns:
            st.subheader("🧩 Cơ cấu loại hư hỏng")
            fig_reason = px.pie(df, names='Lý Do', hole=0.4)
            st.plotly_chart(fig_reason, use_container_width=True)

    # Danh sách máy cần thanh lý
    if not blacklist.empty:
        st.subheader("🚨 Danh sách máy cần thanh lý (Hỏng lặp lại)")
        df_blacklist = df[df["Mã số máy"].isin(blacklist.index)].sort_values("Mã số máy")
        st.dataframe(df_blacklist, use_container_width=True)

    with st.expander("🔍 Chi tiết toàn bộ dữ liệu nhật ký"):
        st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ App chưa nhận được dữ liệu mới từ Google Sheets. Sếp hãy nhấn nút 'LÀM MỚI TOÀN BỘ' ở bên trái nhé!")
