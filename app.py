import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# ID FILE CHUẨN (Lấy từ link Google Sheets mới nhất của sếp)
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
SHEET_NAME = "LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE"

# Link xuất dữ liệu CSV
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=60)
def load_data():
    try:
        # Đọc dữ liệu, ép buộc lấy dòng thứ 2 (header=1) làm tiêu đề để tránh dòng gộp ô
        df = pd.read_csv(URL, header=1)
        
        # Làm sạch tên cột (xóa khoảng trắng dư thừa)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Kiểm tra cột then chốt
        if "Mã số máy" in df.columns:
            df = df.dropna(subset=["Mã số máy"])
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
            
            # Chuyển đổi các cột số
            for col in ["Chi Phí Dự Kiến", "Chi Phí Thực Tế"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        else:
            st.error(f"❌ Vẫn không thấy cột 'Mã số máy'. Cột máy đang đọc được: {list(df.columns)}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {e}")
        return pd.DataFrame()

df = load_data()

# --- GIAO DIỆN ---
st.title("🛡️ Dashboard Quản trị Thiết bị Online")

if not df.empty:
    st.success(f"✅ Đã kết nối thành công dữ liệu từ Google Drive!")
    
    # Dashboard số liệu
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca lỗi", len(df))
    c2.metric("Tổng chi phí thực tế", f"{df['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    counts = df["Mã số máy"].value_counts()
    blacklist = len(counts[counts >= 2])
    c3.metric("Máy hỏng ≥ 2 lần", blacklist, delta="Cần thanh lý", delta_color="inverse")

    # Biểu đồ
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🌎 Lỗi theo Chi nhánh")
        fig_branch = px.bar(df["Chi Nhánh"].value_counts().reset_index(), x='Chi Nhánh', y='count', color='Chi Nhánh', text_auto=True)
        st.plotly_chart(fig_branch, use_container_width=True)
    with col_b:
        st.subheader("🧩 Cơ cấu loại hư hỏng")
        fig_reason = px.pie(df["Lý Do"].value_counts().reset_index(), values='count', names='Lý Do', hole=0.4)
        st.plotly_chart(fig_reason, use_container_width=True)

    # Bảng dữ liệu
    with st.expander("🔍 Xem chi tiết danh sách"):
        st.dataframe(df, use_container_width=True)
else:
    st.info("💡 Sếp nhớ tạo file app.py trên GitHub thay vì dán vào README nhé!")
