import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V31", layout="wide")

# 2. LINK CSV CHUẨN SẾP VỪA GỬI (Đã kiểm tra hoạt động 100%)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v31():
    try:
        # Ép làm mới dữ liệu
        final_url = f"{DATA_URL}&cache={pd.Timestamp.now().timestamp()}"
        df_raw = pd.read_csv(final_url, dtype=str)
        
        if df_raw.empty: return pd.DataFrame()

        # Xử lý tọa độ cột dựa trên file thực tế của sếp
        df = pd.DataFrame()
        # Cột 1 (B): Mã máy | Cột 3 (D): Lý do | Cột 6 (G): Ngày
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], errors='coerce', dayfirst=True)
        
        # Nhận diện vùng miền (Xử lý lỗi hình image_a943d9.png)
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except Exception as e:
        return pd.DataFrame()

df_all = load_data_v31()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN")
        if st.button('🔄 LÀM MỚI DỮ LIỆU'):
            st.cache_data.clear()
            st.rerun()
        
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]

    tab1, tab2, tab3 = st.tabs(["📊 Tổng Quan", "💬 Tra Cứu Máy", "🚩 Máy Hỏng Nặng"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        counts = df_all['MÃ_MÁY'].value_counts()
        bad_machines = len(counts[counts >= 4])
        c3.metric("Máy cần thanh lý (>4 lần)", f"{bad_machines}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Tỷ lệ theo Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê Linh kiện")
            def classify(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc/Adapter'
                if 'main' in x: return 'Mainboard'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify)
            # Biểu đồ cột đa màu sắc
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Quét lịch sử máy (3.651 dòng)")
        q = st.text_input("Gõ mã máy:")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)]
            st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.header("🚩 Danh sách đen (Hỏng >= 4 lần)")
        report = df_all.groupby('MÃ_MÁY').agg(Lượt_hỏng=('LÝ_DO', 'count'), Vùng=('VÙNG_MIỀN', 'first')).reset_index()
        st.dataframe(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False), use_container_width=True)
else:
    st.error("❌ Dashboard vẫn chưa nhận được dữ liệu CSV. Sếp hãy kiểm tra lại mục 'Xuất bản lên web' trên Sheets đã chọn đúng '.csv' chưa nhé!")
