import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# ID FILE & LINK
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
SHEET_NAME = "LAPTOP LỖI - THAY THẾ"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=LAPTOP%20L%E1%BB%96I%20-%20THAY%20TH%E1%BA%BE"

@st.cache_data(ttl=60)
def load_data():
    try:
        # 1. Đọc dữ liệu thô (không lấy tiêu đề)
        raw_df = pd.read_csv(URL, header=None)
        
        # 2. Thuật toán tìm dòng tiêu đề: Quét 10 dòng đầu xem dòng nào có chữ "Mã số máy"
        header_row = 0
        found = False
        for i in range(10):
            if raw_df.iloc[i].astype(str).str.contains("Mã số máy").any():
                header_row = i
                found = True
                break
        
        if not found:
            st.error(f"❌ Vẫn không tìm thấy chữ 'Mã số máy'. Dữ liệu đọc được dòng đầu là: {raw_df.iloc[0].values}")
            return pd.DataFrame()

        # 3. Đọc lại dữ liệu với dòng tiêu đề đã tìm thấy
        df = pd.read_csv(URL, header=header_row)
        
        # 4. Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        # Xử lý nếu có cột trùng lặp do gộp ô
        if "Mã số máy" in df.columns:
            df = df.dropna(subset=["Mã số máy"])
            # Lọc bỏ các dòng tiêu đề bị lặp lại (nếu có)
            df = df[df["Mã số máy"] != "Mã số máy"]
            df["Mã số máy"] = df["Mã số máy"].astype(str).str.strip().str.replace(".0", "", regex=False)
            
            # Chuyển đổi chi phí
            for col in ["Chi Phí Thực Tế", "Chi Phí Dự Kiến"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Lỗi: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success("✅ Đã xử lý xong các cột Unnamed! Kết nối thành công.")
    
    # Chỉ số
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df))
    if "Chi Phí Thực Tế" in df.columns:
        c2.metric("Tổng chi phí", f"{df['Chi Phí Thực Tế'].sum():,.0f} VNĐ")
    
    counts = df["Mã số máy"].value_counts()
    c3.metric("Máy hỏng ≥ 2 lần", len(counts[counts >= 2]))

    # Biểu đồ & Dữ liệu
    st.divider()
    st.subheader("📋 Danh sách chi tiết")
    st.dataframe(df, use_container_width=True)
    
    if "Chi Nhánh" in df.columns:
        st.subheader("🌎 Thống kê theo Chi nhánh")
        fig = px.bar(df["Chi Nhánh"].value_counts().reset_index(), x='Chi Nhánh', y='count', color='Chi Nhánh')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 Đang quét tìm dòng tiêu đề trong Google Sheets...")
