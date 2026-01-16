import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link Google Sheets mới nhất của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
SHEET_NAME = "LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE" # Mã hóa URL tên sheet

# Link xuất dữ liệu CSV từ Google Sheets
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=60) # Cập nhật dữ liệu mỗi 60 giây
def load_data_cloud():
    try:
        # Đọc dữ liệu với header=1 vì dòng 1 của sếp là tiêu đề lớn
        df = pd.read_csv(URL, header=1)
        
        # Làm sạch dữ liệu
        df = df.dropna(subset=["Mã số máy"])
        df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
        
        # Xử lý các cột số (Chi phí)
        for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        return df
    except Exception as e:
        st.error(f"❌ Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_cloud()

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Dashboard Quản lý Thiết bị Online")
st.markdown(f"📍 Đang kết nối trực tiếp với Google Drive")

if not df.empty:
    # 1. Các chỉ số tổng quan
    m1, m2, m3, m4 = st.columns(4)
    
    total_records = len(df)
    total_cost = df["Chi Phí Thực Tế"].sum()
    
    # Đếm số máy hỏng >= 2 lần
    counts = df["Mã số máy"].value_counts()
    blacklist_count = len(counts[counts >= 2])
    
    m1.metric("Tổng ca lỗi", f"{total_records} ca")
    m2.metric("Tổng chi phí sửa", f"{total_cost:,.0f} VNĐ")
    m3.metric("Máy hỏng ≥ 2 lần", f"{blacklist_count} máy", delta="⚠️ Cần thanh lý", delta_color="inverse")
    m4.metric("Chi nhánh lỗi nhất", df["Chi Nhánh"].value_counts().idxmax() if "Chi Nhánh" in df.columns else "N/A")

    st.divider()

    # 2. Biểu đồ phân tích
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌎 Phân bổ lỗi theo Miền")
        if "Chi Nhánh" in df.columns:
            fig_mien = px.bar(df["Chi Nhánh"].value_counts().reset_index(), 
                              x='Chi Nhánh', y='count', color='Chi Nhánh', text_auto=True)
            st.plotly_chart(fig_mien, use_container_width=True)
            
    with col2:
        st.subheader("🔧 Các loại hư hỏng phổ biến")
        if "Lý Do" in df.columns:
            fig_loi = px.pie(df["Lý Do"].value_counts().head(10).reset_index(), 
                             values='count', names='Lý Do', hole=0.4)
            st.plotly_chart(fig_loi, use_container_width=True)

    # 3. Danh sách máy cần thanh lý (Hỏng từ 2 lần trở lên)
    st.subheader("🚨 Danh sách máy 'Đen' (Cần ưu tiên thay thế)")
    df_blacklist = df[df["Mã số máy"].isin(counts[counts >= 2].index)]
    if not df_blacklist.empty:
        st.dataframe(df_blacklist.sort_values(by="Mã số máy"), use_container_width=True)
    else:
        st.success("Chưa phát hiện máy nào hỏng lặp lại.")

    # 4. Tra cứu dữ liệu
    with st.expander("🔍 Xem toàn bộ nhật ký sửa chữa"):
        st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ Đang đợi dữ liệu. Sếp hãy kiểm tra xem Sheet 'LAPTOP LỖI - THAY THẾ' có dữ liệu chưa nhé!")
