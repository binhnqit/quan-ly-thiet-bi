import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link ID từ Google Sheets của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)
def load_data_pro():
    try:
        # Đọc dữ liệu (header=1 để bỏ qua dòng tiêu đề gộp ô to nhất)
        df = pd.read_csv(URL, header=1)
        
        # Chuẩn hóa tên cột: Viết hoa, xóa khoảng trắng
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # 🔍 MAPPING CỘT THÔNG MINH
        col_ma_may = next((c for c in df.columns if "MÁY" in c), None)
        col_khu_vuc = next((c for c in df.columns if "KHU VỰC" in c or "CHI NHÁNH" in c), None)
        col_tinh_trang = next((c for c in df.columns if "TRẠNG" in c or "KIỂM TRA" in c), None)

        if col_ma_may:
            df = df.dropna(subset=[col_ma_may])
            # Làm sạch mã máy (xóa đuôi .0 nếu có)
            df['Mã số máy'] = df[col_ma_may].astype(str).str.split('.').str[0].str.strip()
            
            # Gán cột chuẩn để dùng cho biểu đồ
            df['Khu vực'] = df[col_khu_vuc] if col_khu_vuc else "Chưa phân loại"
            df['Tình trạng'] = df[col_tinh_trang] if col_tinh_trang else "N/A"
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_pro()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro (v7)")

if not df.empty:
    st.success("✅ Dữ liệu đã sẵn sàng!")
    
    # 1. Chỉ số tổng quan
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng ca báo lỗi", len(df))
    
    counts = df['Mã số máy'].value_counts()
    blacklist = counts[counts >= 2]
    m2.metric("Máy hỏng ≥ 2 lần", len(blacklist), delta="⚠️ Cần lưu ý", delta_color="inverse")
    m3.metric("Số khu vực", df['Khu vực'].nunique())

    st.divider()

    # 2. Biểu đồ (Sửa lỗi ValueError tại đây)
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("📍 Thống kê theo Khu vực")
        # Cách vẽ biểu đồ an toàn nhất, không lo lỗi tên cột 'index'
        df_chart = df['Khu vực'].value_counts().reset_index()
        df_chart.columns = ['Tên Khu Vực', 'Số Lượng'] # Đặt tên cố định cho chắc chắn
        
        fig = px.bar(df_chart, x='Tên Khu Vực', y='Số Lượng', 
                     color='Tên Khu Vực', text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("📋 Danh sách sửa chữa mới nhất")
        # Chỉ hiện các cột quan trọng cho gọn
        cols_to_show = ['Mã số máy', 'Khu vực', 'Tình trạng']
        st.dataframe(df[cols_to_show].head(20), use_container_width=True)
        
    # 3. Danh sách máy "đen"
    if not blacklist.empty:
        with st.expander("🚨 CHI TIẾT CÁC MÁY HỎNG LẶP LẠI (CẦN THANH LÝ)"):
            df_blacklist = df[df['Mã số máy'].isin(blacklist.index)]
            st.table(df_blacklist[['Mã số máy', 'Khu vực', 'Tình trạng']].sort_values('Mã số máy'))

else:
    st.info("💡 Đang quét dữ liệu từ Google Sheets... Sếp kiểm tra lại dòng tiêu đề nếu chờ quá lâu nhé.")
    if st.button('🔄 Thử tải lại ngay'):
        st.cache_data.clear()
        st.rerun()
