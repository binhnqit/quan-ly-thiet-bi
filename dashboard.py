import streamlit as st
import pandas as pd
import plotly.express as px
import random

st.set_page_config(page_title="Hệ thống Quản lý Thiết bị Toàn Quốc", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

@st.cache_data(ttl=1)
def load_data_detective():
    try:
        # Ép Google xóa cache để lấy đủ > 3000 dòng
        rid = random.randint(1, 1000000)
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&refresh={rid}"
        
        # Đọc dữ liệu từ dòng đầu tiên để không bỏ sót
        df = pd.read_csv(URL)
        
        # Xử lý lỗi trùng tên cột (Duplicate Column)
        new_cols = []
        counts = {}
        for i, col in enumerate(df.columns):
            c = str(col).strip().upper()
            if not c or "UNNAMED" in c: c = f"COL_{i}"
            if c in counts:
                counts[c] += 1
                new_cols.append(f"{c}_{counts[c]}")
            else:
                counts[c] = 0
                new_cols.append(c)
        df.columns = new_cols

        # --- CHIẾN THUẬT MẮT THẦN: TỰ TÌM CỘT CHỨA MIỀN ---
        def find_region(row):
            row_str = " ".join(row.astype(str).upper())
            if "NAM" in row_str or "MN" in row_str: return "Miền Nam"
            if "BẮC" in row_str or "MB" in row_str: return "Miền Bắc"
            if "TRUNG" in row_str or "ĐN" in row_str or "DN" in row_str: return "Miền Trung"
            return "Khác/Chưa nhập"

        # Quét toàn bộ các cột để xác định vùng miền
        df['VÙNG_PHÂN_LOẠI'] = df.apply(find_region, axis=1)
        
        # Lấy cột mã máy (Thường là cột thứ 2 - Index 1)
        col_ma = df.columns[1]
        df['MÃ_MÁY_FIX'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Lọc bỏ dòng tiêu đề và dòng trống
        df = df[df['MÃ_MÁY_FIX'] != 'nan']
        df = df[~df['MÃ_MÁY_FIX'].str.contains("STT|MÃ", na=False)]
        
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

df = load_data_detective()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    # Tổng dòng bây giờ phải vượt qua 2521
    c1.metric("Tổng số ca ghi nhận", len(df))
    c2.metric("Số máy khác nhau", df['MÃ_MÁY_FIX'].nunique())
    
    val_mn = len(df[df['VÙNG_PHÂN_LOẠI'] == 'Miền Nam'])
    c3.metric("Dữ liệu Miền Nam", val_mn, delta="Đã nhận diện" if val_mn > 0 else "Kiểm tra lại text")

    st.divider()

    # Biểu đồ chuẩn màu sếp thích
    chart_data = df['VÙNG_PHÂN_LOẠI'].value_counts().reset_index()
    chart_data.columns = ['Vùng', 'Số lượng']
    fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                 color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Khác/Chưa nhập": "#6c757d"})
    st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM TRA QUAN TRỌNG
    with st.expander("🔍 Soi dữ liệu dòng cuối cùng"):
        st.write(f"App đang đọc được tổng cộng: **{len(df)}** dòng.")
        st.dataframe(df.tail(100))

else:
    st.info("Sếp đợi vài giây để dữ liệu từ Google Sheets tải về...")
