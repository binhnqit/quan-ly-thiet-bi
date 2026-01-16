import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CẤU HÌNH WEB ---
st.set_page_config(page_title="Hệ thống Quản lý Laptop Cloud", layout="wide")

# Link Google Sheets mới nhất của sếp
SHEET_ID = "1C8P6TWKTvPmQ1EVJYLqR0AhT6HYvz37s"
# Tên sheet phải chính xác từng dấu cách
SHEET_NAME = "LAPTOP LỖI - THAY THẾ" 

# Chuyển đổi link sang định dạng export CSV chuẩn
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE"

@st.cache_data(ttl=60) # Cập nhật mỗi 1 phút cho nóng
def load_data_from_cloud():
    try:
        # Đọc dữ liệu, bỏ qua dòng trống đầu tiên nếu có
        df = pd.read_csv(URL)
        
        # KIỂM TRA DÒNG TIÊU ĐỀ: Nếu dòng đầu không phải "Mã số máy", ta lấy dòng tiếp theo
        if "Mã số máy" not in df.columns:
            df = pd.read_csv(URL, header=1)
            
        # Làm sạch dữ liệu
        df = df.dropna(subset=["Mã số máy"])
        df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
        
        # Chuẩn hóa ngày tháng
        if "Ngày Xác nhận" in df.columns:
            df["Ngày Xác nhận"] = pd.to_datetime(df["Ngày Xác nhận"], errors='coerce')
        
        # Xử lý chi phí
        for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
                
        return df
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {e}")
        return pd.DataFrame()

df = load_data_from_cloud()

# --- GIAO DIỆN ---
st.title("🌐 Hệ thống Quản lý Thiết bị Online (Bản Cloud)")

if not df.empty:
    # Hiển thị thông tin kiểm tra để sếp yên tâm
    with st.expander("✅ Trạng thái kết nối dữ liệu"):
        st.write(f"Đã đọc thành công {len(df)} dòng dữ liệu từ Google Sheets.")
        st.write("Danh sách cột nhận diện được:", list(df.columns))

    # --- PHẦN 1: THỐNG KÊ NHANH ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng ca lỗi", len(df))
    m2.metric("Tổng chi phí sửa", f"{df['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    counts = df["Mã số máy"].value_counts()
    blacklist_num = len(counts[counts >= 2])
    m3.metric("Máy hỏng ≥ 2 lần", f"{blacklist_num} máy", delta="Cần thanh lý", delta_color="inverse")

    st.divider()

    # --- PHẦN 2: BIỂU ĐỒ ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📍 Lỗi theo Chi nhánh")
        fig_branch = px.bar(df["Chi Nhánh"].value_counts().reset_index(), 
                          x='Chi Nhánh', y='count', color='Chi Nhánh', text_auto=True)
        st.plotly_chart(fig_branch, use_container_width=True)
    with c2:
        st.subheader("🧩 Cơ cấu loại lỗi")
        fig_reason = px.pie(df["Lý Do"].value_counts().reset_index(), 
                          values='count', names='Lý Do', hole=0.4)
        st.plotly_chart(fig_reason, use_container_width=True)

    # --- PHẦN 3: DANH SÁCH THANH LÝ ---
    st.subheader("🚨 Danh sách máy 'Đen' (Hỏng nhiều lần)")
    df_rep = df[df["Mã số máy"].isin(counts[counts >= 2].index)]
    st.dataframe(df_rep.sort_values("Mã số máy"), use_container_width=True)

else:
    st.warning("Đang đợi dữ liệu từ Google Sheets... Sếp kiểm tra lại quyền Chia sẻ (Anyone with link) nhé!")
