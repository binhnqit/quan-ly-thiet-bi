import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# ID file và Tên Sheet chuẩn
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
SHEET_NAME = "LAPTOP LỖI - THAY THẾ"
# Link xuất CSV chuẩn
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE"

@st.cache_data(ttl=60)
def load_data():
    try:
        # THUẬT TOÁN TÌM TIÊU ĐỀ: Thử đọc từ dòng 0 đến dòng 5 để tìm cột "Mã số máy"
        for i in range(6): 
            df_test = pd.read_csv(URL, header=i)
            # Chuẩn hóa tên cột: xóa khoảng trắng dư thừa
            df_test.columns = [str(c).strip() for c in df_test.columns]
            
            if "Mã số máy" in df_test.columns:
                # Nếu tìm thấy, xử lý dữ liệu ngay
                df_test = df_test.dropna(subset=["Mã số máy"])
                df_test["Mã số máy"] = df_test["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
                return df_test
        
        # Nếu đã thử 5 dòng đầu mà vẫn không thấy
        st.error("❌ Không tìm thấy cột 'Mã số máy'. Sếp hãy kiểm tra lại tên cột trong file Google Sheets nhé!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi kỹ thuật: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🛡️ Dashboard Quản trị Thiết bị Online")

if not df.empty:
    st.success(f"✅ Đã kết nối thành công! Tìm thấy {len(df)} thiết bị.")
    
    # Chỉ số nhanh
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng lượt lỗi", len(df))
    
    # Xử lý chi phí thực tế (nếu có cột này)
    if "Chi Phí Thực Tế" in df.columns:
        df["Chi Phí Thực Tế"] = pd.to_numeric(df["Chi Phí Thực Tế"], errors='coerce').fillna(0)
        m2.metric("Tổng chi phí", f"{df['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    # Máy hỏng lặp lại
    counts = df["Mã số máy"].value_counts()
    blacklist = counts[counts >= 2].index
    m3.metric("Máy hỏng ≥ 2 lần", len(blacklist))

    # Hiển thị dữ liệu
    st.subheader("📋 Nhật ký sửa chữa")
    st.dataframe(df, use_container_width=True)
    
    # Biểu đồ Chi nhánh
    if "Chi Nhánh" in df.columns:
        st.subheader("🌎 Thống kê theo Chi nhánh")
        fig = px.bar(df["Chi Nhánh"].value_counts().reset_index(), x='Chi Nhánh', y='count', color='Chi Nhánh')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 App đang quét dữ liệu. Nếu vẫn lỗi, sếp hãy chắc chắn trong file Google Sheets của sếp có cột tên chính xác là: Mã số máy")
