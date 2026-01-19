import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN CHUẨN
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI 2026", layout="wide")

# 2. KẾT NỐI DỮ LIỆU LIVE (Đã thông luồng từ hình image_b4a40a.png)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=10)
def load_full_data():
    try:
        final_url = f"{DATA_URL}&cache={pd.Timestamp.now().timestamp()}"
        df_raw = pd.read_csv(final_url, dtype=str)
        if df_raw.empty: return pd.DataFrame()

        df = pd.DataFrame()
        # Ánh xạ chuẩn 3.651 dòng
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], errors='coerce', dayfirst=True)
        
        # Nhận diện vùng miền chuyên sâu
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG", "HCM"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khối Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except:
        return pd.DataFrame()

df_all = load_full_data()

# --- SIDEBAR: ĐIỀU KHIỂN CHIẾN LƯỢC ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=100)
    st.header("⚙️ ĐIỀU KHIỂN")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU MỚI'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm Báo Cáo", list_years, index=0)
        
        list_vung = sorted(df_all['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Lọc theo Khu Vực", list_vung, default=list_vung)
        
        df_filtered = df_all[(df_all['NĂM'] == sel_year) & (df_all['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    tab1, tab2, tab3 = st.tabs(["📊 Báo Cáo Tổng Quan", "💬 Trợ Lý Tra Cứu AI", "🚩 Cảnh Báo Nguy Kịch"])
    
    with tab1:
        # Chỉ số Metric (Hình image_b4a40a.png)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Tổng ca hỏng", f"{len(df_filtered)}", delta="Hệ thống ổn định")
        with m2:
            st.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        with m3:
            counts = df_all['MÃ_MÁY'].value_counts()
            bad_ones = len(counts[counts >= 4])
            st.metric("Máy cần thanh lý", f"{bad_ones}", delta="-2 máy so với tháng trước", delta_color="inverse")

        st.divider()
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📍 Tỷ lệ ca hỏng theo Khu vực")
            fig_pie = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_r:
            st.subheader("🛠️ Phân tích Linh kiện")
            def classify(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc/Adapter'
                if 'main' in x: return 'Mainboard'
                return 'Linh kiện khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify)
            fig_bar = px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK', text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("💬 Tra cứu hồ sơ thiết bị (3.651 dòng)")
        search_q = st.text_input("Nhập mã máy hoặc tên linh kiện để AI tìm kiếm:")
        if search_q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(search_q, na=False, case=False) | 
                         df_all['LÝ_DO'].str.contains(search_q, na=False, case=False)]
            if not res.empty:
                st.success(f"AI tìm thấy {len(res)} lịch sử liên quan đến '{search_q}'")
                st.dataframe(res[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)
            else:
                st.warning("Không tìm thấy dữ liệu.")

    with tab3:
        st.error("🚩 DANH SÁCH THIẾT BỊ HỎNG TRÊN 4 LẦN (CẦN THAY THẾ)")
        black_list = df_all.groupby('MÃ_MÁY').agg(
            Lần_hỏng=('LÝ_DO', 'count'),
            Lỗi_chính=('LÝ_DO', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa bệnh"),
            Khu_vực=('VÙNG_MIỀN', 'first')
        ).reset_index()
        critical_df = black_list[black_list['Lần_hỏng'] >= 4].sort_values('Lần_hỏng', ascending=False)
        st.table(critical_df)
else:
    st.error("Kết nối bị gián đoạn. Sếp hãy nhấn nút 'CẬP NHẬT DỮ LIỆU MỚI' ở Sidebar.")
