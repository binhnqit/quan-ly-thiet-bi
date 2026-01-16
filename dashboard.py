import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link kết nối trực tiếp từ Sheets của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=1)
def load_data_final():
    try:
        # Đọc dữ liệu thô
        df = pd.read_csv(URL)
        
        # 1. Xử lý trùng tên cột ngay lập tức (Xóa lỗi ValueError)
        cols = []
        count = {}
        for col in df.columns:
            c_name = str(col).strip()
            if c_name in count:
                count[c_name] += 1
                cols.append(f"{c_name}_{count[c_name]}")
            else:
                count[c_name] = 0
                cols.append(c_name)
        df.columns = cols

        # 2. Làm sạch tên cột để dễ xử lý logic
        df.columns = [str(c).upper() for c in df.columns]
        
        # 3. Tìm cột Chi Nhánh (Cột F) và Mã Máy
        col_kv = next((c for c in df.columns if any(k in c for k in ["CHI NHÁNH", "KHU VỰC", "CHI NHANH"])), None)
        if not col_kv and len(df.columns) > 5: col_kv = df.columns[5]
        
        col_ma = next((c for c in df.columns if "MÁY" in c or "MASOMAY" in c), None)
        if not col_ma and len(df.columns) > 1: col_ma = df.columns[1]

        # 4. Chuẩn hóa Vùng Miền (Bắt chữ MN cho Miền Nam)
        def fix_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        if col_kv:
            df['VÙNG MIỀN'] = df[col_kv].apply(fix_region)
        
        if col_ma:
            df['MÃ MÁY CHUẨN'] = df[col_ma].astype(str).str.split('.').str[0]
            # Loại bỏ dòng không có mã máy (dòng trống cuối file)
            df = df[df['MÃ MÁY CHUẨN'] != 'nan']
        
        return df, col_kv
    except Exception as e:
        st.error(f"Đang đồng bộ dữ liệu... ({e})")
        return pd.DataFrame(), None

df, real_col = load_data_final()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar
    regions = ["Miền Bắc", "Miền Trung", "Miền Nam", "Khác/Chưa nhập"]
    available = [r for r in regions if r in df['VÙNG MIỀN'].unique()]
    selected = st.sidebar.multiselect("📍 Chọn Miền", regions, default=available)
    
    df_filtered = df[df['VÙNG MIỀN'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy hỏng", df_filtered['MÃ MÁY CHUẨN'].nunique() if 'MÃ MÁY CHUẨN' in df.columns else 0)
    
    val_mn = len(df[df['VÙNG MIỀN'] == 'Miền Nam'])
    c3.metric("Dữ liệu Miền Nam", val_mn, delta="Đã nhận diện" if val_mn > 0 else "Kiểm tra ô MN")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_df = df_filtered['VÙNG MIỀN'].value_counts().reset_index()
        chart_df.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_df, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745"})
        st.plotly_chart(fig, use_container_width=True)

    # Xem dữ liệu thô (Đã fix lỗi Duplicate Column)
    with st.expander("🔍 Soi dữ liệu thô (Dành cho sếp)"):
        st.write(f"Dữ liệu được lấy từ cột: **{real_col}**")
