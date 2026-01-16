import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Thiết bị 3 Miền", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Quét toàn bộ dữ liệu để không sót các dòng MN ở dưới
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&range=A1:Z2000"

@st.cache_data(ttl=20)
def load_data_pro():
    try:
        df = pd.read_csv(URL, header=1)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Tìm các cột quan trọng
        col_ma = next((c for c in df.columns if "MÁY" in c), None)
        col_kv = next((c for c in df.columns if "KHU VỰC" in c or "CHI NHÁNH" in c), None)
        
        if col_ma and col_kv:
            df = df.dropna(subset=[col_ma])
            # CHUẨN HÓA TÊN MIỀN (Fix lỗi MN, DN của sếp)
            def fix_region(name):
                name = str(name).strip().upper()
                if name == 'MN': return 'Miền Nam'
                if name == 'DN': return 'Đà Nẵng'
                if 'BẮC' in name: return 'Miền Bắc'
                if 'TRUNG' in name: return 'Miền Trung'
                if 'NAM' in name: return 'Miền Nam'
                return name

            df['Chi Nhánh'] = df[col_kv].apply(fix_region)
            df['Mã số máy'] = df[col_ma].astype(str).str.split('.').str[0]
            
            # Xử lý chi phí (nếu có)
            df['Tổng phí'] = pd.to_numeric(df.get('SỬA BÊN NGOÀI', 0), errors='coerce').fillna(0)
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_pro()

st.title("🛡️ Dashboard Quản trị Thiết bị Toàn Quốc")

if not df.empty:
    # Sidebar lọc 3 miền
    all_regions = sorted(df['Chi Nhánh'].unique())
    selected = st.sidebar.multiselect("📍 Chọn Miền", all_regions, default=all_regions)
    df_filtered = df[df['Chi Nhánh'].isin(selected)]

    # Hiển thị KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca sửa chữa", len(df_filtered))
    c2.metric("Số máy hỏng (Unique)", df_filtered['Mã số máy'].nunique())
    # Lọc riêng xem Miền Nam có bao nhiêu máy
    sl_mien_nam = len(df[df['Chi Nhánh'] == 'Miền Nam'])
    c3.metric("Riêng Miền Nam (MN)", sl_mien_nam)

    st.divider()

    # Biểu đồ so sánh
    df_chart = df_filtered['Chi Nhánh'].value_counts().reset_index()
    df_chart.columns = ['Vùng Miền', 'Số Ca']
    
    fig = px.bar(df_chart, x='Vùng Miền', y='Số Ca', color='Vùng Miền', 
                 text_auto=True, title="So sánh lỗi giữa các Miền")
    st.plotly_chart(fig, use_container_width=True)

    # Bảng dữ liệu Miền Nam
    if sl_mien_nam > 0:
        with st.expander("📋 Xem danh sách máy Miền Nam (MN)"):
            st.dataframe(df[df['Chi Nhánh'] == 'Miền Nam'][['Mã số máy', 'KHU VỰC', 'TRÌNH TRẠNG']], use_container_width=True)
else:
    st.info("Đang tải dữ liệu từ Google Sheets...")
