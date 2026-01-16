import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link ID chuẩn của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)
def load_data_pro():
    try:
        # Đọc dữ liệu (Bỏ qua 1 dòng tiêu đề to nếu có)
        df = pd.read_csv(URL, header=1)
        
        # CHUẨN HÓA TÊN CỘT: Viết hoa hết để dễ so sánh
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # TỰ ĐỘNG TÌM CỘT (MAPPING)
        # Tìm cột nào có chữ "MÁY" hoặc "MACHINE" hoặc "MASOMAY"
        col_ma_may = next((c for c in df.columns if "MÁY" in c), None)
        col_khu_vuc = next((c for c in df.columns if "KHU VỰC" in c or "CHI NHÁNH" in c), None)
        col_tinh_trang = next((c for c in df.columns if "TRẠNG" in c or "LÝ DO" in c), None)

        if col_ma_may:
            # Loại bỏ dòng trống
            df = df.dropna(subset=[col_ma_may])
            # Làm sạch mã máy
            df["MA_MAY_CLEAN"] = df[col_ma_may].astype(str).str.split('.').str[0].str.strip()
            
            # Gán lại tên chuẩn để code bên dưới xử lý
            df['Mã số máy'] = df["MA_MAY_CLEAN"]
            if col_khu_vuc: df['Khu vực'] = df[col_khu_vuc]
            if col_tinh_trang: df['Tình trạng'] = df[col_tinh_trang]
            
            return df, col_ma_may
        return pd.DataFrame(), None
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {e}")
        return pd.DataFrame(), None

df, col_name = load_data_pro()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro (Cloud Version)")

if not df.empty:
    st.success(f"✅ Đã nhận diện được cột tiêu đề: '{col_name}'")
    
    # Dashboard số liệu
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng ca báo lỗi", len(df))
    
    # Đếm số lần hỏng
    counts = df['Mã số máy'].value_counts()
    blacklist = len(counts[counts >= 2])
    m2.metric("Máy hỏng ≥ 2 lần", blacklist, delta="Cần kiểm tra", delta_color="inverse")
    
    if 'Khu vực' in df.columns:
        m3.metric("Khu vực phát sinh", df['Khu vực'].nunique())

    st.divider()

    # Biểu đồ
    c1, c2 = st.columns(2)
    with c1:
        if 'Khu vực' in df.columns:
            st.subheader("📍 Thống kê theo Khu vực")
            fig = px.bar(df['Khu vực'].value_counts().reset_index(), x='index', y='Khu vực', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("📋 Danh sách máy sửa chữa")
        st.dataframe(df[['Mã số máy', 'Khu vực', 'Tình trạng']] if 'Khu vực' in df.columns else df, use_container_width=True)
        
    # Bảng dữ liệu đầy đủ
    with st.expander("🔍 Xem toàn bộ dữ liệu thô từ Google Sheets"):
        st.write(df)
else:
    st.info("Đang đợi cấu trúc dữ liệu từ Google Sheets...")
    if st.button('🔄 Thử tải lại ngay'):
        st.cache_data.clear()
        st.rerun()
