import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Link xuất dữ liệu thô từ Google
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=1)
def load_data_final_fix():
    try:
        # Đọc dữ liệu (Bỏ qua 2 dòng đầu tiên vì thường là tiêu đề gộp ô to)
        df = pd.read_csv(URL, skiprows=2)
        
        # 1. XỬ LÝ TRÙNG TÊN CỘT (Triệt tiêu lỗi ValueError)
        new_cols = []
        counts = {}
        for col in df.columns:
            c_name = str(col).strip().upper()
            if c_name in counts:
                counts[c_name] += 1
                new_cols.append(f"{c_name}_{counts[c_name]}")
            else:
                counts[c_name] = 0
                new_cols.append(c_name)
        df.columns = new_cols

        # 2. TÌM CỘT DỮ LIỆU CHÍNH (Dựa trên ảnh image_03af91)
        # Cột F thường chứa "Chi Nhánh"
        col_kv = next((c for c in df.columns if "CHI NHÁNH" in c or "KHU VỰC" in c), None)
        # Nếu không tìm thấy theo tên, lấy cột thứ 6 (Index 5 - Cột F)
        if not col_kv and len(df.columns) > 5: col_kv = df.columns[5]
        
        # Cột chứa mã máy (Thường là cột B - Index 1)
        col_ma = next((c for c in df.columns if "MÁY" in c or "SERI" in c), None)
        if not col_ma and len(df.columns) > 1: col_ma = df.columns[1]

        # 3. CHUẨN HÓA MIỀN
        def fix_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Chưa nhập liệu"

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
    regions = ["Miền Bắc", "Miền Trung", "Miền Nam", "Chưa nhập liệu"]
    available = [r for r in regions if r in df['VÙNG MIỀN'].unique()]
    selected = st.sidebar.multiselect("📍 Chọn Miền", regions, default=available)
    
    df_filtered = df[df['VÙNG MIỀN'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy hỏng", df_filtered['MÃ MÁY CHUẨN'].nunique() if 'MÃ MÁY CHUẨN' in df.columns else 0)
    
    val_mn = len(df[df['VÙNG MIỀN'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã nhận" if val_mn > 0 else "Kiểm tra ô màu xanh")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_df = df_filtered['VÙNG MIỀN'].value_counts().reset_index()
        chart_df.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_df, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745"})
        st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM TRA (Dứt điểm lỗi ValueError)
    with st.expander("🔍 Soi dữ liệu thô"):
        st.write(f"Đang đọc dữ liệu từ cột: **{real_col}**")
        # Chỉ hiển thị các cột quan trọng để bảng không bị quá tải
        cols_to_show = [c for c in ['MÃ MÁY CHUẨN', 'VÙNG MIỀN', real_col] if c in df.columns]
        st.dataframe(df[cols_to_show].tail(50))

else:
    st.info("Sếp đợi vài giây để dữ liệu tải về...")
