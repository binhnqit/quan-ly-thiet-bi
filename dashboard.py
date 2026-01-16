import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link ID gốc của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Link xuất dữ liệu sạch nhất, không kèm tham số phụ để tránh lỗi 400
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=2)
def load_data_final_fix():
    try:
        # Đọc dữ liệu từ dòng 2 (Bỏ qua dòng gộp ô đầu tiên)
        df = pd.read_csv(URL, header=1)
        
        # Làm sạch tên cột
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Tìm cột Chi Nhánh bằng cách quét từ khóa hoặc lấy cột thứ 6 (Cột F)
        col_kv = next((c for c in df.columns if any(k in c for k in ["CHI NHÁNH", "KHU VỰC", "CHI NHANH"])), df.columns[5])
        col_ma = next((c for c in df.columns if "MÁY" in c or "MASOMAY" in c), df.columns[1])
        
        # Chuẩn hóa dữ liệu vùng miền (Dành cho Miền Nam, Miền Bắc, Đà Nẵng)
        def fix_region(val):
            v = str(val).strip().upper()
            if any(x in v for x in ['NAM', 'MN', 'SOUTH']): return 'Miền Nam'
            if any(x in v for x in ['BẮC', 'MB', 'NORTH']): return 'Miền Bắc'
            if any(x in v for x in ['TRUNG', 'ĐN', 'DN', 'ĐÀ NẴNG']): return 'Miền Trung'
            return 'Khác/Chưa nhập'

        df['Khu vực'] = df[col_kv].apply(fix_region)
        df['Mã máy'] = df[col_ma].astype(str).str.split('.').str[0]
        
        return df, col_kv
    except Exception as e:
        st.error(f"⚠️ Đang thử kết nối lại... ({e})")
        return pd.DataFrame(), None

df, real_col = load_data_final_fix()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar
    regions = ["Miền Bắc", "Miền Trung", "Miền Nam", "Khác/Chưa nhập"]
    selected = st.sidebar.multiselect("📍 Chọn Miền", regions, default=[r for r in regions if r in df['Khu vực'].unique()])
    
    df_filtered = df[df['Khu vực'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Số máy khác nhau", df_filtered['Mã máy'].nunique())
    
    # Kiểm tra riêng Miền Nam
    num_nam = len(df[df['Khu vực'] == 'Miền Nam'])
    c3.metric("Dữ liệu Miền Nam", num_nam, delta="Đã nhận diện" if num_nam > 0 else "Kiểm tra ô màu xanh!")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_data = df_filtered['Khu vực'].value_counts().reset_index()
        chart_data.columns = ['Vùng', 'Số lượng']
        fig = px.bar(chart_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Bắc": "#007bff", "Miền Trung": "#ffc107", "Miền Nam": "#28a745", "Khác/Chưa nhập": "#6c757d"})
        st.plotly_chart(fig, use_container_width=True)

    # PHẦN QUAN TRỌNG NHẤT: TRÌNH SOI DỮ LIỆU
    with st.expander("🔍 Soi dữ liệu thực tế (Dành cho sếp)"):
        st.write(f"App đang đọc dữ liệu từ cột: **{real_col}**")
        st.write("Dữ liệu 20 dòng cuối cùng (Nơi thường có Miền Nam):")
        st.dataframe(df[[real_col, 'Khu vực']].tail(20))

else:
    st.info("Sếp hãy kiểm tra lại quyền chia sẻ Link Google Sheets (Bất kỳ ai có link đều xem được).")
