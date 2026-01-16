import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link ID từ Google Sheets
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Ép quét 1000 dòng để không sót Miền Nam
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&range=A1:Z1000"

@st.cache_data(ttl=20)
def load_data_final():
    try:
        df = pd.read_csv(URL, header=1)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Mapping cột linh hoạt
        col_ma_may = next((c for c in df.columns if "MÁY" in c), None)
        col_chi_nhanh = next((c for c in df.columns if "CHI NHÁNH" in c or "KHU VỰC" in c), None)
        col_tinh_trang = next((c for c in df.columns if "TRẠNG" in c or "LÝ DO" in c), None)

        if col_ma_may:
            df = df.dropna(subset=[col_ma_may])
            df['Mã số máy'] = df[col_ma_may].astype(str).str.split('.').str[0].str.strip()
            # Xử lý Chi Nhánh (Đảm bảo lấy đủ 3 miền)
            df['Chi Nhánh'] = df[col_chi_nhanh].astype(str).str.strip() if col_chi_nhanh else "Chưa phân loại"
            df = df[~df['Chi Nhánh'].isin(['nan', 'None', ''])]
            
            # Xử lý chi phí sửa chữa
            col_nb = next((c for c in df.columns if "NỘI BỘ" in c), None)
            col_ngoai = next((c for c in df.columns if "NGOÀI" in c), None)
            df['Tổng chi phí'] = 0
            if col_nb: df['Tổng chi phí'] += pd.to_numeric(df[col_nb], errors='coerce').fillna(0)
            if col_ngoai: df['Tổng chi phí'] += pd.to_numeric(df[col_ngoai], errors='coerce').fillna(0)
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame()

df = load_data_final()

st.title("🛡️ Dashboard Quản trị Thiết bị 3 Miền")

if not df.empty:
    # Sidebar lọc
    regions = sorted(df['Chi Nhánh'].unique())
    selected_region = st.sidebar.multiselect("📍 Lọc theo Chi nhánh", options=regions, default=regions)
    df_filtered = df[df['Chi Nhánh'].isin(selected_region)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca lỗi", len(df_filtered))
    c2.metric("Tổng chi phí (VNĐ)", f"{df_filtered['Tổng chi phí'].sum():,.0f}")
    c3.metric("Số máy hỏng lặp lại", len(df_filtered['Mã số máy'].value_counts()[df_filtered['Mã số máy'].value_counts() >= 2]))

    st.divider()

    # Biểu đồ
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Số ca lỗi theo Chi nhánh")
        # --- FIX LỖI VALUEERROR TẠI ĐÂY ---
        df_chart = df_filtered['Chi Nhánh'].value_counts().reset_index()
        # Ép tên cột để Plotly luôn hiểu đúng
        df_chart.columns = ['Vùng Miền', 'Số Ca'] 
        
        fig_bar = px.bar(df_chart, x='Vùng Miền', y='Số Ca', 
                         color='Vùng Miền', text_auto=True,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_b:
        st.subheader("📋 Top máy hỏng nhiều nhất")
        top_bad = df_filtered['Mã số máy'].value_counts().head(10).reset_index()
        top_bad.columns = ['Mã số máy', 'Lần hỏng']
        st.table(top_bad)

    with st.expander("🔍 Chi tiết toàn bộ dữ liệu (3 Miền)"):
        st.dataframe(df_filtered, use_container_width=True)
else:
    st.info("Đang kết nối dữ liệu...")
