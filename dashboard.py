import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ thống Quản lý Laptop Toàn Quốc", layout="wide")

# Link ID gốc của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

@st.cache_data(ttl=5) # Cache cực ngắn để cập nhật liên tục
def load_data_full_sync():
    try:
        # THỦ THUẬT QUAN TRỌNG: Thêm biến thời gian để ép Google nhả dữ liệu mới nhất (vượt qua dòng 2521)
        timestamp = int(time.time())
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&tq&cachebust={timestamp}"
        
        # Đọc dữ liệu thô
        df = pd.read_csv(URL)
        
        # 1. XỬ LÝ TRÙNG TÊN CỘT (Triệt tiêu lỗi ValueError)
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

        # 2. TÌM DỮ LIỆU TẠI CỘT F (Index 5) - Nơi chứa Miền Nam
        # Dựa trên image_04f587, chúng ta cần lùng sục kỹ cột này
        col_kv = df.columns[5] 
        col_ma = df.columns[1] 

        def standardize_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Chưa xác định"

        df['VÙNG MIỀN'] = df[col_kv].apply(standardize_region)
        df['MÃ MÁY'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Chỉ lấy những dòng thực sự có dữ liệu máy
        df = df[df['MÃ MÁY'] != 'nan']
        
        return df, col_kv
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame(), None

df, real_col = load_data_full_sync()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar
    vung_mien = ["Miền Bắc", "Miền Trung", "Miền Nam", "Chưa xác định"]
    selected = st.sidebar.multiselect("📍 Chọn Miền hiển thị", vung_mien, default=vung_mien)
    
    df_filtered = df[df['VÙNG MIỀN'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    # Tổng lượt lỗi giờ đây phải > 3000
    c1.metric("Tổng lượt lỗi thực tế", len(df_filtered))
    c2.metric("Số máy khác nhau", df_filtered['MÃ MÁY'].nunique())
    
    # Số ca Miền Nam
    val_mn = len(df[df['VÙNG MIỀN'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Mới cập nhật" if val_mn > 0 else "Kiểm tra dòng 3000+")

    st.divider()

    # Biểu đồ theo màu image_03af91
    if not df_filtered.empty:
        chart_data = df_filtered['VÙNG MIỀN'].value_counts().reset_index()
        chart_data.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={
                         "Miền Bắc": "#007bff", 
                         "Miền Trung": "#ffc107", 
                         "Miền Nam": "#28a745"
                     })
        st.plotly_chart(fig, use_container_width=True)

    # PHẦN QUAN TRỌNG: XÁC MINH DÒNG 3647
    with st.expander("🔍 Soi dữ liệu dòng cuối (Kiểm tra mốc 3647)"):
        st.write(f"Tổng số dòng App đọc được: **{len(df)}**")
        st.write("Dưới đây là dữ liệu mới nhất ở cuối file:")
        st.dataframe(df[['MÃ MÁY', 'VÙNG MIỀN', real_col]].tail(100))

else:
    st.warning("Đang chờ Google nhả dữ liệu mới... Sếp nhấn F5 sau 5 giây nhé!")
