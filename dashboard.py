import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link ID gốc của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Sử dụng phương thức xuất dữ liệu trực tiếp, bỏ qua mọi bộ đệm (cache) của Google
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

@st.cache_data(ttl=1) # Cập nhật ngay lập tức mỗi giây
def load_data_final_victory():
    try:
        # Đọc dữ liệu thô
        df = pd.read_csv(URL)
        
        # Làm sạch tên cột và loại bỏ cột rỗng
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
        
        # Tìm cột Chi Nhánh (Thường là cột F - index 5)
        # Nếu sếp đổi tên, code vẫn sẽ tự tìm từ khóa
        col_kv = next((c for c in df.columns if any(k in c for k in ["CHI NHÁNH", "KHU VỰC", "CHI NHANH"])), df.columns[5])
        col_ma = next((c for c in df.columns if "MÁY" in c or "MASOMAY" in c), df.columns[1])

        def standardize_region(val):
            v = str(val).strip().upper()
            # Quét mọi biến thể có thể có của Miền Nam
            if any(x in v for x in ["NAM", "MN", "SOUTH", "MIỀN NAM"]): return "Miền Nam"
            if any(x in v for x in ["BẮC", "MB", "NORTH", "MIỀN BẮC"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN", "CENTER"]): return "Miền Trung"
            return "Chưa phân loại"

        df['Khu Vực'] = df[col_kv].apply(standardize_region)
        df['Mã máy'] = df[col_ma].astype(str).str.split('.').str[0]
        
        # Loại bỏ các dòng trống hoàn toàn
        df = df[df['Mã máy'] != 'nan']
        
        return df, col_kv
    except Exception as e:
        st.error(f"Đang đồng bộ lại với Sheets... ({e})")
        return pd.DataFrame(), None

df, real_col = load_data_final_victory()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar
    regions = ["Miền Bắc", "Miền Trung", "Miền Nam", "Chưa phân loại"]
    # Chỉ hiện các miền thực sự có trong dữ liệu hiện tại
    available = [r for r in regions if r in df['Khu Vực'].unique()]
    selected = st.sidebar.multiselect("📍 Chọn Miền", regions, default=available)
    
    df_filtered = df[df['Khu Vực'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy hỏng", df_filtered['Mã máy'].nunique())
    
    # Kiểm tra số ca Miền Nam thực tế
    val_mn = len(df[df['Khu Vực'] == 'Miền Nam'])
    c3.metric("Số ca Miền Nam", val_mn, delta="Đã nhận" if val_mn > 0 else "Kiểm tra Sheets")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_df = df_filtered['Khu Vực'].value_counts().reset_index()
        chart_df.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_df, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745", "Chưa phân loại": "#6c757d"})
        st.plotly_chart(fig, use_container_width=True)

    # 🔍 SOI LỖI CHO SẾP
    with st.expander("🛠️ Xem 100 dòng dữ liệu cuối cùng"):
        st.write(f"App đang đọc dữ liệu từ cột: {real_col}")
        # Hiện 100 dòng cuối để sếp thấy dòng Miền Nam có chữ hay không
        st.dataframe(df.tail(100))

else:
    st.info("Vui lòng đợi vài giây để dữ liệu từ Google Sheets đổ về Dashboard...")
