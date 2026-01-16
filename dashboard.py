import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Đọc toàn bộ file không giới hạn dòng
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=2)
def load_data_final_perfect():
    try:
        # Đọc dữ liệu từ dòng có tiêu đề (Dòng 1 trong file Sheets)
        df = pd.read_csv(URL, header=1)
        
        # 1. Dọn dẹp cột rác
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.columns = [str(c).strip().upper() for c in df.columns]

        # 2. Tìm cột "Chi Nhánh" linh hoạt
        col_kv = next((c for c in df.columns if any(k in c for k in ["CHI NHÁNH", "KHU VỰC", "CHI NHANH"])), None)
        col_ma = next((c for c in df.columns if "MÁY" in c or "MASOMAY" in c), None)

        if col_kv:
            # Thuật toán tìm Miền Nam trong mọi dòng
            def detect_region(val):
                v = str(val).strip().upper()
                if any(x in v for x in ["MIỀN NAM", "MIEN NAM", "MN", "NAM"]): return "Miền Nam"
                if any(x in v for x in ["MIỀN BẮC", "MIEN BAC", "MB", "BẮC"]): return "Miền Bắc"
                if any(x in v for x in ["TRUNG", "ĐN", "DN", "ĐÀ NẴNG"]): return "Miền Trung"
                return "Khác/Chưa nhập"

            df['Khu Vực'] = df[col_kv].apply(detect_region)
            # Lấy mã máy chuẩn
            if col_ma:
                df['Mã máy'] = df[col_ma].astype(str).str.split('.').str[0]
            
            return df, col_kv
        return pd.DataFrame(), None
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame(), None

df, found_col = load_data_final_perfect()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar lọc
    regions = ["Miền Bắc", "Miền Trung", "Miền Nam", "Khác/Chưa nhập"]
    # Chỉ hiện những miền thực sự có dữ liệu để sếp dễ chọn
    actual_regions = [r for r in regions if r in df['Khu Vực'].unique()]
    selected = st.sidebar.multiselect("📍 Chọn Miền", actual_regions, default=actual_regions)
    
    df_filtered = df[df['Khu Vực'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy khác nhau", df_filtered['Mã máy'].nunique() if 'Mã máy' in df.columns else 0)
    
    # Đếm riêng Miền Nam để sếp đối chiếu
    val_mn = len(df[df['Khu Vực'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã nhận diện" if val_mn > 0 else "Vẫn chưa thấy dòng MN")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_df = df_filtered['Khu Vực'].value_counts().reset_index()
        chart_df.columns = ['Vùng', 'Số ca']
        fig = px.bar(chart_df, x='Vùng', y='Số ca', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745", "Khác/Chưa nhập": "#6c757d"})
        st.plotly_chart(fig, use_container_width=True)

    # PHẦN KIỂM CHỨNG CHO SẾP
    with st.expander("🔍 Soi dữ liệu thô (Dành cho sếp)"):
        st.write(f"Đang đọc dữ liệu từ cột: **{found_col}**")
        st.write("Dữ liệu 50 dòng cuối cùng trong file (nơi thường có Miền Nam):")
        st.dataframe(df[[found_col, 'Khu Vực']].tail(50))

else:
    st.info("Sếp ơi, hãy kiểm tra cột 'Chi Nhánh' trong file Sheets xem đã có chữ 'Miền Nam' hoặc 'MN' chưa nhé!")
