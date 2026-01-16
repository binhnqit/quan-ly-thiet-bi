import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=1)
def load_data_safe():
    try:
        df = pd.read_csv(URL)
        
        # --- XỬ LÝ TRÙNG TÊN CỘT (FIX LỖI VALUEERROR) ---
        cols = pd.Series(df.columns)
        for i, col in enumerate(df.columns):
            if cols[i:].list().count(col) > 1:
                cols[i] = f"{col}_{i}"
        df.columns = cols
        
        # Làm sạch tên cột
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Xác định cột Khu vực (thường là cột F - index 5)
        # Quét tên cột để tìm "CHI NHÁNH" hoặc "KHU VỰC"
        col_kv = next((c for c in df.columns if any(k in c for k in ["CHI NHÁNH", "KHU VỰC", "CHI NHANH"])), None)
        if not col_kv and len(df.columns) > 5: col_kv = df.columns[5]
        
        col_ma = next((c for c in df.columns if "MÁY" in c or "MASOMAY" in c), None)
        if not col_ma and len(df.columns) > 1: col_ma = df.columns[1]

        def standardize_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN", "SOUTH"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB", "NORTH"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        if col_kv:
            df['Khu Vực'] = df[col_kv].apply(standardize_region)
        
        if col_ma:
            df['Mã máy'] = df[col_ma].astype(str).str.split('.').str[0]
            df = df[df['Mã máy'] != 'nan']
        
        return df, col_kv
    except Exception as e:
        st.error(f"Đang đồng bộ... ({e})")
        return pd.DataFrame(), None

df, real_col = load_data_safe()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar lọc
    vung_mien_list = ["Miền Bắc", "Miền Trung", "Miền Nam", "Khác/Chưa nhập"]
    available = [r for r in vung_mien_list if r in df['Khu Vực'].unique()]
    selected = st.sidebar.multiselect("📍 Chọn Miền", vung_mien_list, default=available)
    
    df_filtered = df[df['Khu Vực'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy hỏng", df_filtered['Mã máy'].nunique() if 'Mã máy' in df.columns else 0)
    
    val_mn = len(df[df['Khu Vực'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã nhận diện" if val_mn > 0 else "Kiểm tra Sheets")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_df = df_filtered['Khu Vực'].value_counts().reset_index()
        chart_df.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_df, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745"})
        st.plotly_chart(fig, use_container_width=True)

    # Xem dữ liệu
    with st.expander("🔍 Kiểm tra 100 dòng cuối"):
        # Chỉ hiển thị các cột quan trọng để tránh bảng quá rộng
        st.dataframe(df.tail(100))

else:
    st.info("Sếp đợi chút để dữ liệu tải về nhé...")
