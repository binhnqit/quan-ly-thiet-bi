import streamlit as st
import pandas as pd
import plotly.express as px
import random

st.set_page_config(page_title="Hệ thống Quản lý Thiết bị Toàn Quốc", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

@st.cache_data(ttl=1)
def load_data_final_v2():
    try:
        # Ép Google xóa cache bằng số ngẫu nhiên để lấy đủ > 3000 dòng
        rid = random.randint(1, 1000000)
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&refresh={rid}"
        
        # Đọc dữ liệu từ dòng đầu tiên
        df = pd.read_csv(URL)
        
        # 1. XỬ LÝ TRÙNG TÊN CỘT (Triệt tiêu lỗi ValueError)
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

        # 2. CHIẾN THUẬT QUÉT TỪNG DÒNG (Đã fix lỗi .upper())
        def find_region_safe(row):
            # Chuyển toàn bộ dòng thành 1 chuỗi văn bản duy nhất để quét
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["MIỀN NAM", " NAM ", " MN ", "NAM"]): return "Miền Nam"
            if any(x in text for x in ["MIỀN BẮC", " BẮC ", " MB ", "BẮC"]): return "Miền Bắc"
            if any(x in text for x in ["MIỀN TRUNG", " TRUNG ", " ĐN ", " DN "]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df.apply(find_region_safe, axis=1)
        
        # Lấy cột Mã máy (Thường là cột thứ 2 - Index 1)
        col_ma = df.columns[1]
        df['MÃ_MÁY_FIX'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Lọc bỏ dòng tiêu đề và dòng trống
        df = df[df['MÃ_MÁY_FIX'] != 'nan']
        df = df[~df['MÃ_MÁY_FIX'].str.contains("STT|MÃ", na=False)]
        
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

df = load_data_final_v2()

st.title("🛡️ Dashboard Quản trị Thiết bị Toàn Quốc")

if not df.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số dòng thực tế", len(df))
    c2.metric("Số máy khác nhau", df['MÃ_MÁY_FIX'].nunique())
    
    val_mn = len(df[df['VÙNG_MIỀN'] == 'Miền Nam'])
    c3.metric("Dữ liệu Miền Nam", val_mn)

    st.divider()

    # Biểu đồ
    chart_data = df['VÙNG_MIỀN'].value_counts().reset_index()
    chart_data.columns = ['Vùng', 'Số lượng']
    fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                 color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
    st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM TRA QUAN TRỌNG
    with st.expander("🔍 Soi dữ liệu dòng cuối cùng (Kiểm tra mốc 3647)"):
        st.write(f"App đang đọc được tổng cộng: **{len(df)}** dòng.")
        st.dataframe(df.tail(100))

else:
    st.info("Sếp đợi vài giây để dữ liệu tải về...")
