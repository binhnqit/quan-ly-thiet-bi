import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V22", layout="wide")

# 2. LINK DỮ LIỆU ĐÃ XÁC THỰC TỪ ẢNH CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v22():
    try:
        # Ép kiểu string toàn bộ khi đọc để tránh lỗi định dạng hỗn hợp
        raw_df = pd.read_csv(f"{DATA_URL}&cache_bust={pd.Timestamp.now().timestamp()}", dtype=str)
        
        # Tạo khung dữ liệu sạch
        df = pd.DataFrame()
        
        # Tọa độ cột chuẩn theo Google Sheets thực tế của sếp
        df['MÃ_MÁY'] = raw_df.iloc[:, 1].str.split('.').str[0].str.strip() # Cột B: Mã Máy
        df['LÝ_DO'] = raw_df.iloc[:, 3].fillna("Chưa xác định") # Cột D: Lý do hỏng
        df['NGAY_FIX'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce', dayfirst=True) # Cột G: Ngày sửa
        
        # Nhận diện vùng miền linh hoạt từ nội dung dòng
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"
        
        df['VÙNG_MIỀN'] = raw_df.apply(detect_vung, axis=1)
        
        # Loại bỏ các dòng lỗi ngày tháng và phân loại
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df_all = load_data_v22()

# --- SIDEBAR QUẢN TRỊ ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU (3.651 DÒNG)'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        # Tự động chọn năm 2026 hoặc năm mới nhất
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0)
        
        list_vung = sorted(df_all['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        
        df_filtered = df_all[(df_all['NĂM'] == sel_year) & (df_all['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    tab1, tab2, tab4, tab3 = st.tabs(["📊 Dashboard", "💬 Chatbot AI", "🚩 Máy Nguy Kịch", "📖 Hướng Dẫn"])

    with tab1:
        # THẺ KPI CHUẨN (Khắc phục lỗi treo)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng (Lọc)", f"{len(df_filtered)}")
        c2.metric("Số lượng thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        # Máy nguy kịch (Tính trên toàn file 3.651 dòng)
        bad_machines = df_all['MÃ_MÁY'].value_counts()
        crit_count = len(bad_machines[bad_machines >= 4])
        c3.metric("Tổng máy cần thanh lý", f"{crit_count}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Phân bổ hỏng theo Miền")
            fig_pie = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with cr:
            st.subheader("🛠️ Thống kê linh kiện hỏng")
            # Sửa lỗi biểu đồ linh kiện bị dồn vào "Khác"
            def phân_loại_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'main' in x: return 'Mainboard'
                if 'sạc' in x or 'adapter' in x: return 'Sạc/Adapter'
                if 'ổ' in x or 'ssd' in x: return 'Ổ cứng'
                return 'Linh kiện khác'
            
            df_filtered['LINH_KIỆN'] = df_filtered['LÝ_DO'].apply(phân_loại_lk)
            counts = df_filtered['LINH_KIỆN'].value_counts().reset_index()
            fig_bar = px.bar(counts, x='count', y='LINH_KIỆN', orientation='h', color='LINH_KIỆN', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("💬 Tra cứu hồ sơ máy (Quét 3.651 dòng)")
        q = st.text_input("Gõ mã máy để AI truy lục lịch sử bảo trì:")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)].sort_values('NGAY_FIX', ascending=False)
            if not res.empty:
                st.success(f"Dữ liệu Live: Máy {q} đã sửa {len(res)} lần.")
                st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']], use_container_width=True)
            else:
                st.warning(f"Mã máy {q} không có trong lịch sử hỏng hóc.")

    with tab4:
        st.header("🚩 Danh Sách Đen: Thiết bị hỏng hệ thống")
        report = df_all.groupby('MÃ_MÁY').agg(
            Số_lần_hỏng=('LÝ_DO', 'count'),
            Bệnh_nền=('LÝ_DO', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa bệnh"),
            Khu_vực=('VÙNG_MIỀN', 'first')
        ).reset_index()
        # Hiển thị máy hỏng từ 4 lần trở lên
        st.dataframe(report[report['Số_lần_hỏng'] >= 4].sort_values('Số_lần_hỏng', ascending=False), use_container_width=True, hide_index=True)

else:
