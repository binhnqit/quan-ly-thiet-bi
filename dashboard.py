import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN EXECUTIVE
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản V80", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { font-weight: bold; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v80():
    try:
        # Load dữ liệu thô tuyệt đối không bỏ dòng
        url = f"{DATA_URL}&cache={time.time()}"
        df = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("Chưa xác định")
        
        # Dò cột thông minh theo trọng số
        cols = df.columns.tolist()
        c_ma = next((c for c in cols if any(k in c.upper() for k in ['MÃ', 'ID', 'SERIAL'])), cols[1])
        c_ly = next((c for c in cols if any(k in c.upper() for k in ['LỖI', 'LÝ DO', 'HỎNG', 'TÌNH TRẠNG'])), cols[3])
        c_ng = next((c for c in cols if any(k in c.upper() for k in ['NGÀY', 'DATE', 'THỜI GIAN'])), cols[0])
        c_kh = next((c for c in cols if any(k in c.upper() for k in ['KHÁCH', 'ĐƠN VỊ', 'TÊN'])), cols[2])

        # Tạo bảng chuẩn - Giữ nguyên 100% số dòng
        final_df = pd.DataFrame({
            'MÃ_MÁY': df[c_ma].astype(str).str.strip(),
            'LINH_KIỆN': df[c_ly].astype(str).str.strip(),
            'KHÁCH_HÀNG': df[c_kh].astype(str).str.strip(),
            'NGÀY_GỐC': df[c_ng]
        })

        # Xử lý ngày tháng linh hoạt để không mất dòng
        final_df['NGÀY_DT'] = pd.to_datetime(final_df['NGÀY_GỐC'], dayfirst=True, errors='coerce')
        final_df['NĂM'] = final_df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        final_df['THÁNG_NUM'] = final_df['NGÀY_DT'].dt.month.fillna(0).astype(int)
        
        # Phân loại vùng miền AI-driven
        def get_region(kh):
            v = str(kh).upper()
            if any(x in v for x in ['BẮC', 'HN', 'PHÚ', 'SƠN']): return 'MIỀN BẮC'
            if any(x in v for x in ['TRUNG', 'ĐÀ NẴNG', 'HUẾ']): return 'MIỀN TRUNG'
            return 'MIỀN NAM'
        final_df['VÙNG_MIỀN'] = final_df['KHÁCH_HÀNG'].apply(get_region)

        return final_df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ CONTROL CENTER")
    if st.button('🔄 SYNC DATA (LÀM MỚI 100%)', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v80()
    if data is not None:
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Năm", ["Tất cả"] + [int(y) for y in y_list])
        
        m_options = ["Tất cả (Cộng dồn)"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Tháng", m_options)

        # LOGIC LỌC KHÔNG MẤT DỮ LIỆU
        df_display = data.copy()
        if sel_year != "Tất cả": 
            df_display = df_display[df_display['NĂM'] == sel_year]
        if sel_month != "Tất cả (Cộng dồn)":
            m_val = int(sel_month.replace("Tháng ", ""))
            df_display = df_display[df_display['THÁNG_NUM'] == m_val]

# --- MAIN DASHBOARD ---
if data is not None:
    st.title("📊 HỆ THỐNG PHÂN TÍCH TÀI SẢN DOANH NGHIỆP")
    
    # KPI CHUẨN
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng ca hỏng", f"{len(df_display):,}")
    k2.metric("Thiết bị lỗi", f"{df_display['MÃ_MÁY'].nunique():,}")
    counts = df_display['MÃ_MÁY'].value_counts()
    k3.metric("Máy hỏng tái diễn", len(counts[counts > 1]))
    k4.metric("Đơn vị/Khách hàng", df_display['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3, tab4 = st.tabs(["📈 BÁO CÁO TỔNG QUAN", "🔍 TRUY XUẤT CHI TIẾT", "🤖 TRỢ LÝ AI (LIVE)", "📖 NHẬT KÝ HỆ THỐNG"])

    with tab1:
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.subheader("TOP 10 LINH KIỆN HỎNG NHIỀU NHẤT")
            top_lk = df_display['LINH_KIỆN'].value_counts().head(10)
            st.bar_chart(top_lk)
        with c_right:
            st.subheader("PHÂN BỔ VÙNG MIỀN")
            fig = px.pie(df_display, names='VÙNG_MIỀN', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig, use_container_width=True)
            

    with tab2:
        search = st.text_input("🔍 Nhập mã máy hoặc tên đơn vị để truy xuất:")
        if search:
            res = df_display[df_display.apply(lambda row: search.upper() in row.astype(
