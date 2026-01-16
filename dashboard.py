import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Thiết bị Pro", layout="wide")

# Link xuất dữ liệu sạch nhất
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=1)
def load_data_final_fix():
    try:
        # Bỏ qua 2 dòng đầu để tránh tiêu đề gộp ô to
        df = pd.read_csv(URL, skiprows=2)
        
        # --- FIX LỖI DUPLICATE COLUMN ---
        new_cols = []
        counts = {}
        for i, col in enumerate(df.columns):
            c_name = str(col).strip().upper()
            if not c_name or "UNNAMED" in c_name: c_name = f"COL_{i}"
            if c_name in counts:
                counts[c_name] += 1
                new_cols.append(f"{c_name}_{counts[c_name]}")
            else:
                counts[c_name] = 0
                new_cols.append(c_name)
        df.columns = new_cols

        # --- DÙNG TỌA ĐỘ CỨNG ĐỂ LẤY DỮ LIỆU ---
        # Cột B (index 1) là Mã Máy, Cột F (index 5) là Chi Nhánh
        col_ma = df.columns[1] 
        col_kv = df.columns[5] 

        def standardize_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Chưa xác định"

        df['VÙNG MIỀN'] = df[col_kv].apply(standardize_region)
        df['MÃ MÁY'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Lọc bỏ dòng trống
        df = df[df['MÃ MÁY'] != 'nan']
        
        return df, col_kv
    except Exception as e:
        st.error(f"Đang đồng bộ... ({e})")
        return pd.DataFrame(), None

df, real_col_name = load_data_final_fix()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar
    regions = ["Miền Bắc", "Miền Trung", "Miền Nam", "Chưa xác định"]
    selected = st.sidebar.multiselect("📍 Chọn Miền", regions, default=[r for r in regions if r in df['VÙNG MIỀN'].unique()])
    
    df_filtered = df[df['VÙNG MIỀN'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy hỏng", df_filtered['MÃ MÁY'].nunique())
    
    # Kiểm tra riêng Miền Nam
    val_mn = len(df[df['VÙNG MIỀN'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã nhận" if val_mn > 0 else "Cần check ô màu xanh")

    st.divider()

    # Biểu đồ gộp màu theo image_03af91
    if not df_filtered.empty:
        chart_df = df_filtered['VÙNG MIỀN'].value_counts().reset_index()
        chart_df.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_df, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={
                         "Miền Bắc": "#8B0000",   # Đỏ đậm
                         "Miền Trung": "#DEB887", # Vàng nâu
                         "Miền Nam": "#006400"    # Xanh lá đậm
                     })
        st.plotly_chart(fig, use_container_width=True)

    # PHẦN QUAN TRỌNG: SOI DỮ LIỆU
    with st.expander("🔍 Soi dữ liệu thô (Dành cho sếp)"):
        st.write(f"Đang bốc dữ liệu tại cột F: **{real_col_name}**")
        st.dataframe(df[['MÃ MÁY', 'VÙNG MIỀN', real_col_name]].tail(50))

else:
    st.info("Sếp đợi vài giây để dữ liệu tải về nhé...")
