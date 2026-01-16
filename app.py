import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# ID file Google Sheets mới nhất sếp vừa gửi
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Tên Sheet chính xác (Mã hóa URL để tránh lỗi dấu tiếng Việt)
SHEET_NAME = "LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE"

# Link xuất dữ liệu CSV chuẩn từ Google Sheets
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=60)
def load_data():
    try:
        # Đọc dữ liệu (Sếp để tiêu đề ở dòng 2 nên dùng header=1)
        df = pd.read_csv(URL, header=1)
        
        # 1. Làm sạch dữ liệu
        # Loại bỏ các dòng trống không có Mã số máy
        df = df.dropna(subset=["Mã số máy"])
        
        # Chuẩn hóa Mã số máy
        df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
        
        # 2. Xử lý các cột tài chính (Nếu có)
        for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
                
        return df
    except Exception as e:
        st.error(f"❌ Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df = load_data()

# --- GIAO DIỆN DASHBOARD ---
st.title("🛡️ Dashboard Quản trị Thiết bị Online")
st.markdown(f"📍 **Dữ liệu:** [Kết nối Google Drive thành công]")

if not df.empty:
    # PHẦN 1: CHỈ SỐ TỔNG QUAN
    m1, m2, m3, m4 = st.columns(4)
    
    total_cases = len(df)
    total_spent = df["Chi Phí Thực Tế"].sum()
    
    # Đếm máy hỏng trên 2 lần để báo thanh lý
    counts = df["Mã số máy"].value_counts()
    blacklist_count = len(counts[counts >= 2])
    
    m1.metric("Tổng ca lỗi", f"{total_cases}")
    m2.metric("Tổng chi phí", f"{total_spent:,.0f} VNĐ")
    m3.metric("Máy hỏng ≥ 2 lần", f"{blacklist_count}", delta="Cần thay", delta_color="inverse")
    m4.metric("Khu vực lỗi nhất", df["Chi Nhánh"].value_counts().idxmax() if "Chi Nhánh" in df.columns else "N/A")

    st.divider()

    # PHẦN 2: BIỂU ĐỒ PHÂN TÍCH
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🌎 Lỗi theo Chi nhánh")
        if "Chi Nhánh" in df.columns:
            fig_branch = px.bar(df["Chi Nhánh"].value_counts().reset_index(), 
                              x='Chi Nhánh', y='count', color='Chi Nhánh', text_auto=True)
            st.plotly_chart(fig_branch, use_container_width=True)
            
    with col2:
        st.subheader("🔧 Loại hư hỏng phổ biến")
        if "Lý Do" in df.columns:
            fig_reason = px.pie(df["Lý Do"].value_counts().head(10).reset_index(), 
                              values='count', names='Lý Do', hole=0.4)
            st.plotly_chart(fig_reason, use_container_width=True)

    # PHẦN 3: DANH SÁCH THANH LÝ
    st.subheader("🚨 Danh sách máy cần thanh lý (Hỏng lặp lại)")
    df_blacklist = df[df["Mã số máy"].isin(counts[counts >= 2].index)]
    if not df_blacklist.empty:
        st.dataframe(df_blacklist.sort_values(by="Mã số máy"), use_container_width=True)
    else:
        st.success("Chưa phát hiện máy nào hỏng lặp lại. Dàn máy hiện tại khá ổn định!")

    # PHẦN 4: NHẬT KÝ CHI TIẾT
    with st.expander("🔍 Xem toàn bộ nhật ký sửa chữa"):
        st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ Đang đợi dữ liệu. Sếp hãy kiểm tra lại xem trong Sheet 'LAPTOP LỖI - THAY THẾ' đã có nội dung chưa nhé.")
