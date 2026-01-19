import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V33", layout="wide")

# 2. CẬP NHẬT LINK CSV THEO YÊU CẦU CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=10)
def load_data_v33():
    try:
        final_url = f"{DATA_URL}&cache={pd.Timestamp.now().timestamp()}"
        df_raw = pd.read_csv(final_url, dtype=str)
        if df_raw.empty: return pd.DataFrame()

        df = pd.DataFrame()
        # Ánh xạ cột chuẩn (Cột B: Mã máy, D: Lý do, G: Ngày)
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], errors='coerce', dayfirst=True)
        
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
    except:
        return pd.DataFrame()

df_all = load_data_v33()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🔄 LÀM MỚI HỆ THỐNG'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💬 Trợ Lý AI", "🚩 Máy Nguy Kịch", "📖 Hướng Dẫn"])
    
    with tab1:
        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        m2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        counts = df_all['MÃ_MÁY'].value_counts()
        m3.metric("Máy hỏng nặng", f"{len(counts[counts >= 4])}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Linh kiện hỏng")
            def classify(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Trợ lý tra cứu hồ sơ máy")
        q = st.text_input("Gõ mã máy để AI truy lục (VD: 3534):")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)]
            if not res.empty:
                st.success(f"AI tìm thấy {len(res)} lần bảo trì của máy {q}")
                st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)
            else:
                st.warning("Không tìm thấy mã máy này trong hệ thống.")

    with tab3:
        st.error("🚩 CẢNH BÁO THAY THẾ: MÁY HỎNG >= 4 LẦN")
        report = df_all.groupby('MÃ_MÁY').agg(Lượt_hỏng=('LÝ_DO', 'count'), Vùng=('VÙNG_MIỀN', 'first')).reset_index()
        st.dataframe(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False), use_container_width=True)

    with tab4:
        st.info("📖 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG")
        st.markdown("""
        1. **Cập nhật dữ liệu:** Khi sếp sửa Google Sheets, hãy nhấn nút **'LÀM MỚI HỆ THỐNG'** ở Sidebar trái.
        2. **Tra cứu máy:** Sử dụng Tab **'Trợ Lý AI'**, gõ mã máy để xem toàn bộ lịch sử sửa chữa trước khi duyệt mua linh kiện mới.
        3. **Quản lý hỏng nặng:** Tab **'Máy Nguy Kịch'** tự động liệt kê những máy có tần suất hỏng cao để sếp đưa ra quyết định thanh lý.
        4. **Lọc dữ liệu:** Dùng bộ lọc năm ở Sidebar để xem báo cáo theo từng giai đoạn.
        """)
else:
    st.error("⚠️ Hệ thống chưa nhận được dữ liệu. Sếp kiểm tra lại link CSV nhé!")
