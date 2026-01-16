import streamlit as st
import pandas as pd
import plotly.express as px

# Cấu hình trang
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link Google Sheets (Dùng ID chuẩn sếp đã share Anyone with link)
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Link xuất CSV trực tiếp (Bỏ qua các tham số rườm rà để tăng tốc)
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10) # Chỉ cache 10 giây để sếp thấy thay đổi ngay
def load_data():
    try:
        # Đọc trực tiếp dòng 1 làm tiêu đề (sau khi sếp đã xóa dòng gộp ô)
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        # Kiểm tra cột then chốt
        if "Mã số máy" in df.columns:
            df = df.dropna(subset=["Mã số máy"])
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
            
            # Chuyển đổi chi phí sang số
            for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {e}")
        return pd.DataFrame()

# Nút bấm tải lại thủ công để sếp không phải đợi
if st.button('🔄 Cập nhật dữ liệu mới nhất'):
    st.cache_data.clear()
    st.rerun()

df = load_data()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success(f"✅ Đã kết nối thành công! Tổng cộng: {len(df)} bản ghi.")
    
    # 1. Các chỉ số quan trọng
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df))
    c2.metric("Tổng chi phí thực tế", f"{df['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    counts = df["Mã số máy"].value_counts()
    blacklist = counts[counts >= 2]
    c3.metric("Máy cần thanh lý (Hỏng ≥ 2)", len(blacklist))

    # 2. Biểu đồ
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🌎 Lỗi theo Chi nhánh")
        fig_branch = px.bar(df["Chi Nhánh"].value_counts().reset_index(), x='index', y='Chi Nhánh', 
                            labels={'index':'Chi Nhánh', 'Chi Nhánh':'Số ca'}, text_auto=True)
        st.plotly_chart(fig_branch, use_container_width=True)
    with col_b:
        st.subheader("🧩 Cơ cấu loại hư hỏng")
        fig_reason = px.pie(df, names='Lý Do', hole=0.4)
        st.plotly_chart(fig_reason, use_container_width=True)

    # 3. Danh sách máy hỏng nhiều
    if len(blacklist) > 0:
        st.subheader("🚨 Danh sách máy hỏng lặp lại")
        st.dataframe(df[df["Mã số máy"].isin(blacklist.index)], use_container_width=True)

    # 4. Bảng dữ liệu thô
    with st.expander("🔍 Chi tiết toàn bộ nhật ký"):
        st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ Không tìm thấy dữ liệu. Sếp hãy xóa dòng 1 (dòng tiêu đề xanh gộp ô) trong Google Sheets rồi nhấn nút Cập nhật phía trên nhé!")
