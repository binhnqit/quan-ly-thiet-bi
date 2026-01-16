import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình giao diện
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# 2. Link Google Sheets (ID lấy từ hình của sếp)
# Sử dụng link export trực tiếp để bỏ qua việc quét tên Sheet rườm rà
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # Cập nhật dữ liệu sau mỗi 10 giây
def load_data_fast():
    try:
        # Đọc trực tiếp dòng 1 làm tiêu đề
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột (loại bỏ khoảng trắng dư thừa)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Kiểm tra cột then chốt
        if "Mã số máy" in df.columns:
            # Loại bỏ dòng trống không có mã máy
            df = df.dropna(subset=["Mã số máy"])
            # Chuyển mã máy về dạng chữ để tránh lỗi hiển thị số thập phân
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().replace(r'\.0$', '', regex=True)
            
            # Chuyển đổi các cột chi phí sang số
            for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Kết nối thất bại: {e}")
        return pd.DataFrame()

# Nút cập nhật thủ công ở Sidebar
if st.sidebar.button('🔄 Làm mới dữ liệu'):
    st.cache_data.clear()
    st.rerun()

df = load_data_fast()

# --- GIAO DIỆN DASHBOARD ---
st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success(f"✅ Đã kết nối thành công dữ liệu từ Google Drive!")
    
    # PHẦN 1: CHỈ SỐ TỔNG QUAN
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng ca lỗi", len(df))
    
    # Tính toán chi phí nếu có cột
    total_cost = df["Chi Phí Thực Tế"].sum() if "Chi Phí Thực Tế" in df.columns else 0
    m2.metric("Tổng chi phí thực tế", f"{total_cost:,.0f} VNĐ")
    
    # Tìm máy hỏng lặp lại
    counts = df["Mã số máy"].value_counts()
    blacklist_num = len(counts[counts >= 2])
    m3.metric("Máy hỏng ≥ 2 lần", f"{blacklist_num} thiết bị", delta="Cần thanh lý", delta_color="inverse")

    st.divider()

    # PHẦN 2: BIỂU ĐỒ TRỰC QUAN
    col_a, col_b = st.columns(2)
    with col_a:
        if "Chi Nhánh" in df.columns:
            st.subheader("🌎 Lỗi theo Chi nhánh")
            fig_branch = px.bar(df["Chi Nhánh"].value_counts().reset_index(), 
                                x='index', y='Chi Nhánh', 
                                labels={'index':'Chi Nhánh', 'Chi Nhánh':'Số ca'},
                                color='index', text_auto=True)
            st.plotly_chart(fig_branch, use_container_width=True)
        
    with col_b:
        if "Lý Do" in df.columns:
            st.subheader("🧩 Phân loại hư hỏng")
            fig_reason = px.pie(df, names='Lý Do', hole=0.4)
            st.plotly_chart(fig_reason, use_container_width=True)

    # PHẦN 3: DANH SÁCH MÁY "ĐEN"
    st.subheader("🚨 Danh sách máy hỏng lặp lại (Danh mục thanh lý)")
    df_rep = df[df["Mã số máy"].isin(counts[counts >= 2].index)]
    if not df_rep.empty:
        st.dataframe(df_rep.sort_values("Mã số máy"), use_container_width=True)
    else:
        st.info("Chưa phát hiện máy nào hỏng lặp lại.")

    # PHẦN 4: CHI TIẾT
    with st.expander("🔍 Xem toàn bộ nhật ký dữ liệu"):
        st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ App đã kết nối nhưng chưa tìm thấy cột 'Mã số máy'. Sếp nhấn nút 'Làm mới dữ liệu' ở bên trái nhé!")
