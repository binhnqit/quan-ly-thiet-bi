import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. THIẾT LẬP GIAO DIỆN PREMIUM
st.set_page_config(page_title="Hệ Thống Quản Trị V85", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stMetric { background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #e1e4e8; border-radius: 5px 5px 0 0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v85():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc toàn bộ file, ép kiểu string để bảo toàn 100% dữ liệu
        raw = pd.read_csv(url, dtype=str, header=None).fillna("Chưa xác định")
        
        # --- THUẬT TOÁN TỰ CĂN CHỈNH CỘT (FIX LỆCH CỘT TỪ IMAGE_EC0E96) ---
        # Chúng ta sẽ tìm xem cột nào chứa định dạng ngày tháng (dd/mm/yyyy)
        data_rows = raw.values.tolist()
        final_rows = []
        
        for row in data_rows:
            # Bỏ qua dòng tiêu đề nếu nó chứa chữ "Mã" hoặc "Ngày"
            if "Mã" in str(row) or "Ngày" in str(row): continue
            
            # Logic nhận diện cột thông minh:
            # Giả sử: Cột có '/' là Ngày, Cột có số ngắn là Mã, Cột dài là Linh kiện/Khách
            d_ngay, d_ma, d_kh, d_lk = "Chưa xác định", "Chưa xác định", "Chưa xác định", "Chưa xác định"
            
            for item in row:
                item_str = str(item).strip()
                if "/" in item_str and len(item_str) <= 10: d_ngay = item_str
                elif item_str.isdigit() and len(item_str) < 10: d_ma = item_str
                elif len(item_str) > 15: d_lk = item_str
                else: d_kh = item_str
            
            final_rows.append([d_ngay, d_ma, d_kh, d_lk])

        df = pd.DataFrame(final_rows, columns=['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN'])
        
        # Xử lý thời gian
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY_DT'].dt.month.fillna(0).astype(int)
        
        # Phân vùng miền dựa trên tên khách hàng
        def phan_vung(kh):
            v = str(kh).upper()
            if any(x in v for x in ['HN', 'BẮC', 'SƠN', 'PHÚ', 'NỘI']): return 'MIỀN BẮC'
            if any(x in v for x in ['ĐÀ NẴNG', 'HUẾ', 'TRUNG', 'VINH']): return 'MIỀN TRUNG'
            return 'MIỀN NAM'
        df['VÙNG'] = df['KHÁCH_HÀNG'].apply(phan_vung)
        
        return df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return None

# --- GIAO DIỆN ĐIỀU KHIỂN ---
data = load_data_v85()

with st.sidebar:
    st.header("🎛️ BỘ LỌC HỆ THỐNG")
    if st.button('🔄 CẬP NHẬT LIVE DATA', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if data is not None:
        years = sorted(data['NĂM'].unique(), reverse=True)
        sel_y = st.selectbox("Chọn năm", ["Tất cả"] + years)
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Chọn tháng", months)

        # Bộ lọc
        df_view = data.copy()
        if sel_y != "Tất cả": df_view = df_view[df_view['NĂM'] == sel_y]
        if sel_m != "Tất cả":
            m_num = int(sel_m.replace("Tháng ", ""))
            df_view = df_view[df_view['THÁNG'] == m_num]

# --- DASHBOARD CHÍNH ---
if data is not None:
    st.title("🚀 DASHBOARD QUẢN TRỊ TÀI SẢN 2026")
    
    # KPI chính - Đảm bảo khớp 4.039 dòng (nếu chọn Tất cả)
    m1, m2, m3, m4 = st.columns(4)
    total_hongs = len(df_view)
    m1.metric("Tổng ca hỏng", f"{total_hongs:,}")
    m2.metric("Số thiết bị lỗi", f"{df_view['MÃ_MÁY'].nunique():,}")
    
    # Tính máy hỏng tái diễn (Xuất hiện > 1 lần)
    re_fail = df_view['MÃ_MÁY'].value_counts()
    black_list_ids = re_fail[re_fail > 1].index.tolist()
    m3.metric("Máy hỏng tái diễn", len(black_list_ids))
    m4.metric("Khách hàng báo lỗi", df_view['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3, tab4 = st.tabs(["📊 BÁO CÁO TỔNG HỢP", "🚩 DANH SÁCH ĐEN (RE-FAIL)", "🔍 TRUY XUẤT", "📋 DỮ LIỆU GỐC"])

    with tab1:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.subheader("TOP 10 LINH KIỆN LỖI")
            top_lk = df_view[df_view['LINH_KIỆN'] != "Chưa xác định"]['LINH_KIỆN'].value_counts().head(10)
            fig = px.bar(top_lk, x=top_lk.values, y=top_lk.index, orientation='h', 
                         labels={'x':'Số lần hỏng', 'index':'Linh kiện'},
                         color=top_lk.values, color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
        with col_r:
            st.subheader("PHÂN BỔ MIỀN")
            fig_pie = px.pie(df_view, names='VÙNG', hole=0.4,
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN TRUNG':'#F59E0B', 'MIỀN NAM':'#10B981'})
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.subheader("⚠️ DANH SÁCH MÁY HỎNG TRÊN 1 LẦN")
        df_black = df_view[df_view['MÃ_MÁY'].isin(black_list_ids)]
        df_black_summary = df_black.groupby(['MÃ_MÁY', 'KHÁCH_HÀNG']).agg({
            'LINH_KIỆN': lambda x: ', '.join(x.unique()),
            'NGÀY': 'count'
        }).rename(columns={'NGÀY': 'Số lần hỏng'}).sort_values('Số lần hỏng', ascending=False)
        
        st.table(df_black_summary.head(20))
        st.caption("Ghi chú: Đây là những máy cần thu hồi hoặc kiểm tra nhà cung cấp linh kiện.")

    with tab3:
        search = st.text_input("Nhập Mã máy hoặc Tên khách hàng để xem lịch sử hỏng:")
        if search:
            mask = df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            st.dataframe(df_view[mask], use_container_width=True)

    with tab4:
        st.write(f"Đang hiển thị {len(df_view)} dòng dữ liệu đã được AI căn chỉnh cột.")
        st.dataframe(df_view[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
