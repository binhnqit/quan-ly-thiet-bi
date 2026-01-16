import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Thiết bị Toàn Quốc", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Ép quét 2000 dòng để đảm bảo không sót dữ liệu Miền Nam ở dưới cùng
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&range=A1:Z2000"

@st.cache_data(ttl=10)
def load_data_ultra():
    try:
        df = pd.read_csv(URL, header=1)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        col_ma = next((c for c in df.columns if "MÁY" in c), None)
        col_kv = next((c for c in df.columns if "KHU VỰC" in c or "CHI NHÁNH" in c), None)
        
        if col_ma and col_kv:
            df = df.dropna(subset=[col_ma])
            
            # HÀM CHUẨN HÓA SIÊU CẤP: Gộp ĐN vào Đà Nẵng, MN vào Miền Nam
            def normalize_region(val):
                v = str(val).strip().upper()
                if v in ['MN', 'MIỀN NAM', 'MIEN NAM', 'NAM']: return 'Miền Nam'
                if v in ['DN', 'ĐÀ NẴNG', 'DA NANG', 'TRUNG']: return 'Miền Trung/Đà Nẵng'
                if v in ['MB', 'MIỀN BẮC', 'MIEN BAC', 'BẮC']: return 'Miền Bắc'
                return v if v != 'NAN' else 'Chưa phân loại'

            df['Chi Nhánh Chuẩn'] = df[col_kv].apply(normalize_region)
            df['Mã số máy'] = df[col_ma].astype(str).str.split('.').str[0]
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame()

df = load_data_ultra()

st.title("🛡️ Dashboard Quản trị Thiết bị Toàn Quốc")

if not df.empty:
    # Sidebar lọc thông minh
    options = sorted(df['Chi Nhánh Chuẩn'].unique())
    selected = st.sidebar.multiselect("📍 Chọn Miền", options, default=options)
    df_filtered = df[df['Chi Nhánh Chuẩn'].isin(selected)]

    # Hiển thị KPI chính xác
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca sửa chữa", len(df_filtered))
    c2.metric("Số máy hỏng (Unique)", df_filtered['Mã số máy'].nunique())
    
    # Đếm chính xác Miền Nam
    mien_nam_count = len(df[df['Chi Nhánh Chuẩn'] == 'Miền Nam'])
    c3.metric("Dữ liệu Miền Nam", mien_nam_count, delta="Đã đồng bộ MN" if mien_nam_count > 0 else "Chưa thấy dữ liệu")

    st.divider()

    # Biểu đồ gộp (Không còn tình trạng hiện cả ĐN và Đà Nẵng riêng biệt)
    df_chart = df_filtered['Chi Nhánh Chuẩn'].value_counts().reset_index()
    df_chart.columns = ['Vùng Miền', 'Số Ca']
    
    fig = px.bar(df_chart, x='Vùng Miền', y='Số Ca', color='Vùng Miền', 
                 text_auto=True, title="Thống kê lỗi gộp theo Miền")
    st.plotly_chart(fig, use_container_width=True)

    # Bảng kiểm tra dành riêng cho sếp
    with st.expander("🔍 Kiểm tra dữ liệu Miền Nam (MN)"):
        df_mn = df[df['Chi Nhánh Chuẩn'] == 'Miền Nam']
        if not df_mn.empty:
            st.write(f"Tìm thấy {len(df_mn)} dòng thuộc Miền Nam:")
            st.dataframe(df_mn[['Mã số máy', 'Chi Nhánh Chuẩn']], use_container_width=True)
        else:
            st.warning("Vẫn chưa tìm thấy dòng nào có giá trị 'MN' hoặc 'Miền Nam' trong cột Chi Nhánh.")
else:
    st.info("Sếp hãy kiểm tra lại quyền chia sẻ Link Google Sheets nhé!")
