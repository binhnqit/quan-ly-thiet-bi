import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Pro", layout="wide")

# Link ID gốc của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Link này cực kỳ sạch, Google sẽ không bao giờ báo lỗi 400
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=5)
def load_data_final_fix():
    try:
        # Đọc dữ liệu (Bỏ qua dòng gộp ô đầu tiên)
        df = pd.read_csv(URL, header=1)
        
        # Làm sạch tên cột
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # DÙNG VỊ TRÍ CỘT ĐỂ ĐỌC (Tránh lỗi do sếp đổi tên cột)
        # Theo file của sếp: Cột 2 (index 1) là Mã máy, Cột 6 (index 5) là Chi nhánh
        col_ma = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        col_kv = df.columns[5] if len(df.columns) > 5 else df.columns[0]
        
        # Loại bỏ các dòng hoàn toàn trống
        df = df.dropna(subset=[col_ma])
        
        # CHUẨN HÓA MIỀN (Gộp MN về Miền Nam)
        def fix_mien(val):
            v = str(val).strip().upper()
            if any(x in v for x in ['NAM', 'MN']): return 'MIỀN NAM'
            if any(x in v for x in ['BẮC', 'MB']): return 'MIỀN BẮC'
            if any(x in v for x in ['TRUNG', 'ĐN', 'DN', 'ĐÀ NẴNG']): return 'MIỀN TRUNG/ĐÀ NẴNG'
            return 'KHÁC'

        df['Vùng Miền'] = df[col_kv].apply(fix_mien)
        df['Mã số máy'] = df[col_ma].astype(str).str.split('.').str[0]
        
        return df, col_kv
    except Exception as e:
        st.error(f"⚠️ Đang kết nối lại... ({e})")
        return pd.DataFrame(), None

df, real_col_name = load_data_final_fix()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar lọc
    vung_list = sorted(df['Vùng Miền'].unique())
    selected = st.sidebar.multiselect("📍 Chọn Miền", vung_list, default=vung_list)
    df_filtered = df[df['Vùng Miền'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số lượng máy hỏng", df_filtered['Mã số máy'].nunique())
    
    # Kiểm tra Miền Nam
    num_nam = len(df[df['Vùng Miền'] == 'MIỀN NAM'])
    c3.metric("Số ca Miền Nam", num_nam)

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_data = df_filtered['Vùng Miền'].value_counts().reset_index()
        chart_data.columns = ['Khu vực', 'Số lượng']
        fig = px.bar(chart_data, x='Khu vực', y='Số lượng', color='Khu vực', text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    # TRÌNH SOI DỮ LIỆU ĐỂ SẾP KIỂM TRA
    with st.expander("🔍 Kiểm tra dữ liệu cột Chi Nhánh (Cột F)"):
        st.write(f"Dữ liệu App đang thấy ở cột '{real_col_name}':")
        st.write(df['Vùng Miền'].value_counts())
        st.write("10 dòng dữ liệu cuối cùng trong file:")
        st.dataframe(df[['Mã số máy', 'Vùng Miền']].tail(10))

else:
    st.info("Sếp hãy kiểm tra: 1. File đã nhấn Chia sẻ (Bất kỳ ai có link)? 2. Internet ổn định chứ?")
