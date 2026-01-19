import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V39", layout="wide")

# 2. LINK CSV CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v39():
    try:
        # Cơ chế ép làm mới dữ liệu
        sync_url = f"{DATA_URL}&nocache={time.time()}"
        df_raw = pd.read_csv(sync_url, on_bad_lines='skip', dtype=str)
        
        if df_raw.empty: return None

        # --- THUẬT TOÁN TÌM CỘT THÔNG MINH ---
        # Tự tìm cột chứa từ khóa thay vì chỉ định cột số 1, 3, 6
        col_ma = col_lydo = col_ngay = None
        for i, col in enumerate(df_raw.columns):
            c_upper = str(col).upper()
            if "MÃ" in c_upper or "MA" in c_upper: col_ma = i
            if "LÝ" in c_upper or "LY" in c_upper or "DO" in c_upper: col_lydo = i
            if "NGÀY" in c_upper or "NGAY" in c_upper: col_ngay = i

        # Nếu không tìm thấy theo tên, dùng mặc định theo cấu trúc file của sếp
        col_ma = col_ma if col_ma is not None else 1
        col_lydo = col_lydo if col_lydo is not None else 3
        col_ngay = col_ngay if col_ngay is not None else 6

        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw.iloc[:, col_ma].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, col_lydo].fillna("Chưa rõ")
        
        # XỬ LÝ NGÀY THÁNG CỰC MẠNH (Fix lỗi 0 dòng)
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, col_ngay], dayfirst=True, errors='coerce')
        
        # Nhận diện vùng miền
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG", "HCM"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khối Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        
        # Giữ lại dữ liệu hợp lệ
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year.astype(int)
        return df
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu: {e}")
        return None

df_all = load_data_v39()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ VIÊN")
    if st.button('🔄 LÀM MỚI TOÀN BỘ'):
        st.cache_data.clear()
        st.rerun()
    
    if df_all is not None and len(df_all) > 0:
        st.success(f"✅ Đã kết nối {len(df_all)} dòng")
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm Báo Cáo", list_years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]
    else:
        st.warning("⚠️ Đang kiểm tra dữ liệu...")
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # KHÔI PHỤC ĐẦY ĐỦ 4 TAB NHƯ SẾP CẦN
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💬 Trợ Lý AI", "🚩 Cảnh Báo", "📖 Hướng Dẫn"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        counts = df_all['MÃ_MÁY'].value_counts()
        c3.metric("Máy hỏng nặng (>4 lần)", f"{len(counts[counts >= 4])}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Tỷ lệ theo Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê Linh kiện")
            def classify_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc/Adapter'
                return 'Linh kiện khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Trợ lý AI Tra cứu Lịch sử")
        search = st.text_input("Gõ mã máy hoặc tên lỗi (VD: 3534):")
        if search:
            res = df_all[df_all['MÃ_MÁY'].str.contains(search, na=False, case=False) | 
                         df_all['LÝ_DO'].str.contains(search, na=False, case=False)]
            st.dataframe(res[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Máy cần thanh lý gấp")
        report = df_all.groupby('MÃ_MÁY').agg(Lượt_hỏng=('LÝ_DO', 'count'), Vùng=('VÙNG_MIỀN', 'first')).reset_index()
        st.table(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False))

    with tab4:
        st.info("📖 HƯỚNG DẪN SỬ DỤNG")
        st.markdown("""
        1. **Dữ liệu:** Hệ thống tự động lấy từ Google Sheets của sếp. Nhấn 'Làm mới' nếu sếp vừa nhập thêm dòng.
        2. **AI:** Dùng Tab 'Trợ lý AI' để kiểm tra xem một máy đã sửa những gì trong quá khứ.
        3. **Lưu ý:** Nếu thấy '0 dòng', hãy kiểm tra cột 'Ngày sửa' trong Sheets xem có đúng định dạng Ngày/Tháng/Năm không.
        """)
else:
    st.error("❌ Không tìm thấy dữ liệu hợp lệ. Sếp hãy nhấn 'Làm mới' hoặc kiểm tra cột 'Ngày sửa' trong file Sheets.")
