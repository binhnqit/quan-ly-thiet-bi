import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Thiết bị Pro", layout="wide")

# Link ID từ Google Sheets
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Thêm tham số range=A1:Z1000 để ép Google trả về toàn bộ dữ liệu 3 miền
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&range=A1:Z1000"

@st.cache_data(ttl=30)
def load_data_triple_regions():
    try:
        # Đọc dữ liệu (bỏ qua dòng tiêu đề gộp ô đầu tiên)
        df = pd.read_csv(URL, header=1)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Mapping cột linh hoạt theo dữ liệu thực tế của sếp
        col_ma_may = next((c for c in df.columns if "MÁY" in c), None)
        col_chi_nhanh = next((c for c in df.columns if "CHI NHÁNH" in c or "KHU VỰC" in c), None)
        col_tinh_trang = next((c for c in df.columns if "TRẠNG" in c or "LÝ DO" in c), None)
        col_phi_nb = next((c for c in df.columns if "NỘI BỘ" in c), None)
        col_phi_ngoai = next((c for c in df.columns if "NGOÀI" in c), None)

        if col_ma_may:
            # Chỉ lấy những dòng thực sự có Mã số máy
            df = df.dropna(subset=[col_ma_may])
            df['Mã số máy'] = df[col_ma_may].astype(str).str.split('.').str[0].str.strip()
            
            # Xử lý Chi Nhánh (Đảm bảo lấy đủ Miền Nam, Miền Trung, Miền Bắc)
            df['Chi Nhánh'] = df[col_chi_nhanh].astype(str).str.strip() if col_chi_nhanh else "Chưa phân loại"
            # Loại bỏ các giá trị rác hoặc dòng trống bị hiểu nhầm là chuỗi 'nan'
            df = df[~df['Chi Nhánh'].isin(['nan', 'None', ''])]
            
            # Xử lý chi phí
            df['Tổng chi phí'] = 0
            for c in [col_phi_nb, col_phi_ngoai]:
                if c:
                    df['Tổng chi phí'] += pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame()

df = load_data_triple_regions()

# --- GIAO DIỆN ---
st.title("🛡️ Dashboard Quản trị Thiết bị 3 Miền")

if not df.empty:
    # Sidebar lọc nhanh
    selected_region = st.sidebar.multiselect("📍 Lọc theo Miền", 
                                            options=sorted(df['Chi Nhánh'].unique()),
                                            default=sorted(df['Chi Nhánh'].unique()))
    
    df_filtered = df[df['Chi Nhánh'].isin(selected_region)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt lỗi", len(df_filtered))
    c2.metric("Tổng chi phí (VNĐ)", f"{df_filtered['Tổng chi phí'].sum():,.0f}")
    c3.metric("Số lượng máy hỏng", df_filtered['Mã số máy'].nunique())

    st.divider()

    # Biểu đồ 3 Miền
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Số ca lỗi theo Chi nhánh")
        fig_bar = px.bar(df_filtered['Chi Nhánh'].value_counts().reset_index(), 
                         x='index', y='Chi Nhánh', color='index', text_auto=True,
                         labels={'index': 'Chi Nhánh', 'Chi Nhánh': 'Số ca'})
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_b:
        st.subheader("📋 Danh sách máy Miền Nam mới nhất")
        df_south = df_filtered[df_filtered['Chi Nhánh'].str.contains("Nam")]
        st.dataframe(df_south[['Mã số máy', 'Chi Nhánh', 'Tổng chi phí']].head(10), use_container_width=True)

    # Bảng tổng hợp
    with st.expander("🔍 Xem chi tiết toàn bộ dữ liệu"):
        st.dataframe(df_filtered, use_container_width=True)
else:
    st.warning("Đang quét dữ liệu... Sếp đợi chút nhé!")
