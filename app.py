import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình giao diện chuyên nghiệp
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# 2. Link Google Sheets (ID mới nhất từ hình của sếp)
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Dùng link xuất trực tiếp để tốc độ tải nhanh nhất
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # Cập nhật cực nhanh sau 10 giây
def load_data_lightning():
    try:
        # Đọc thẳng dòng 1 làm tiêu đề vì sếp đã chỉnh file quá chuẩn
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột (xóa khoảng trắng dư)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Kiểm tra và xử lý dữ liệu
        if "Mã số máy" in df.columns:
            # Loại bỏ dòng trống
            df = df.dropna(subset=["Mã số máy"])
            # Chuẩn hóa mã máy thành chữ
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
            
            # Chuyển đổi chi phí sang số để làm biểu đồ
            for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Kết nối thất bại: {e}")
        return pd.DataFrame()

# Nút cập nhật thủ công
if st.sidebar.button('🔄 Làm mới dữ liệu'):
    st.cache_data.clear()
    st.rerun()

df = load_data_lightning()

# --- GIAO DIỆN DASHBOARD ---
st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success(f"✅ Đã kết nối thành công! Hệ thống đang quản lý {len(df)} lượt sửa chữa.")
    
    # PHẦN 1: CHỈ SỐ TÀI CHÍNH & VẬN HÀNH
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng ca lỗi", len(df))
    m2.metric("Tổng chi phí", f"{df['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    counts = df["Mã số máy"].value_counts()
    blacklist_num = len(counts[counts >= 2])
    m3.metric("Máy hỏng ≥ 2 lần", blacklist_num, delta="Cần thanh lý", delta_color="inverse")
    m4.metric("Khu vực nóng nhất", df["Chi Nhánh"].value_counts().idxmax() if "Chi Nhánh" in df.columns else "N/A")

    st.divider()

    # PHẦN 2: BIỂU ĐỒ TRỰC QUAN
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🌎 Lỗi theo Chi nhánh")
        fig_branch = px.bar(df["Chi Nhánh"].value_counts().reset_index(), 
                            x='index', y='Chi Nhánh', labels={'index':'Chi Nhánh', 'Chi Nhánh':'Số ca'},
                            color='index', text_auto=True)
        st.plotly_chart(fig_branch, use_container_width=True)
        
    with col_b:
        st.subheader("🧩 Phân loại hư hỏng")
        fig_reason = px.pie(df, names='Lý Do', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_reason, use_container_width=True)

    # PHẦN 3: DANH SÁCH CẦN XỬ LÝ
    st.subheader("🚨 Danh sách máy hỏng lặp lại (Danh mục thanh lý)")
    df_rep = df[df["Mã số máy"].isin(counts[counts >= 2].index)]
    st.dataframe(df_rep.sort_values("Mã số máy"), use_container_width=True)

    with st.expander("🔍 Chi tiết toàn bộ nhật ký (Dữ liệu từ Google Sheets)"):
        st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ Không tìm thấy cột 'Mã số máy'. Sếp hãy kiểm tra lại file Google Sheets nhé!")
