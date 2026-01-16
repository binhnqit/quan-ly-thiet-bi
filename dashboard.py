import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link kết nối trực tiếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=1)
def load_data_final_fix():
    try:
        df = pd.read_csv(URL)
        
        # --- FIX LỖI TRÙNG TÊN CỘT (PHƯƠNG ÁN AN TOÀN NHẤT) ---
        new_cols = []
        counts = {}
        for col in df.columns:
            if col in counts:
                counts[col] += 1
                new_cols.append(f"{col}_{counts[col]}")
            else:
                counts[col] = 0
                new_cols.append(col)
        df.columns = new_cols
        
        # Làm sạch tên cột
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Tìm cột Chi Nhánh (Cột F) và Mã Máy
        col_kv = next((c for c in df.columns if any(k in c for k in ["CHI NHÁNH", "KHU VỰC", "CHI NHANH"])), None)
        if not col_kv and len(df.columns) > 5: col_kv = df.columns[5]
        
        col_ma = next((c for c in df.columns if "MÁY" in c or "MASOMAY" in c), None)
        if not col_ma and len(df.columns) > 1: col_ma = df.columns[1]

        # Chuẩn hóa Vùng Miền
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
            df = df[df['MÃ MÁY CHUẨN'] != 'nan']
        
        return df, col_kv
    except Exception as e:
        st.error(f"Đang đồng bộ... ({e})")
        return pd.DataFrame(), None

df, real_col = load_data_final_fix()

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
    c3.metric("Số ca Miền Nam", val_mn, delta="OK" if val_mn > 0 else "Kiểm tra ô màu xanh")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_df = df_filtered['VÙNG MIỀN'].value_counts().reset_index()
        chart_df.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_df, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745"})
        st.plotly_chart(fig, use_container_width=True)

    # Xem 100 dòng cuối (Quan trọng nhất để soi Miền Nam)
    with st.expander("🔍 Soi dữ liệu thô (Dành cho sếp)"):
        st.write(f"Đang đọc dữ liệu từ cột: **{real_col}**")
        st.dataframe(df.tail(100))

else:
    st.info("Vui lòng đợi vài giây để dữ liệu tải về...")
