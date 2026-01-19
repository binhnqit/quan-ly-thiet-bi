import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V27", layout="wide")

# 2. XỬ LÝ LINK DỮ LIỆU THÔNG MINH
# Link gốc sếp copy từ Google
RAW_LINK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pubhtml"

# AI tự động chuyển đổi sang định dạng CSV nếu sếp lỡ dán link pubhtml
if "pubhtml" in RAW_LINK:
    DATA_URL = RAW_LINK.replace("pubhtml", "pub?output=csv")
else:
    DATA_URL = RAW_LINK

@st.cache_data(ttl=10)
def load_data_v27():
    try:
        # Ép làm mới dữ liệu bằng timestamp
        final_url = f"{DATA_URL}&t={pd.Timestamp.now().timestamp()}"
        raw_df = pd.read_csv(final_url, dtype=str)
        
        if raw_df.empty: return pd.DataFrame()

        df = pd.DataFrame()
        # Định vị cột: B (Mã Máy), D (Lý do), G (Ngày sửa)
        df['MÃ_MÁY'] = raw_df.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = raw_df.iloc[:, 3].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce', dayfirst=True)
        
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "VP Công Ty"
        
        df['VÙNG_MIỀN'] = raw_df.apply(detect_vung, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except Exception as e:
        st.error(f"⚠️ Lỗi đọc dữ liệu: Có thể link 'Publish to web' đã bị thay đổi hoặc hết hạn. Lỗi: {e}")
        return pd.DataFrame()

df_all = load_data_v27()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛡️ QUẢN TRỊ DỮ LIỆU")
    if st.button('🔄 ÉP LÀM MỚI 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0)
        list_vung = sorted(df_all['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        df_filtered = df_all[(df_all['NĂM'] == sel_year) & (df_all['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💬 Tra cứu AI", "🚩 Máy Nguy Kịch"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng lượt hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        bad_counts = df_all['MÃ_MÁY'].value_counts()
        crit_count = len(bad_counts[bad_counts >= 4])
        c3.metric("Máy cần thanh lý", f"{crit_count}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Phân bổ theo Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê linh kiện")
            def classify_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'main' in x: return 'Mainboard'
                if 'sạc' in x or 'adapter' in x: return 'Sạc/Adapter'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Tra cứu hồ sơ (3.651 dòng)")
        q = st.text_input("Gõ mã máy:")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)]
            if not res.empty:
                st.success(f"Dữ liệu máy {q}:")
                st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.header("🚩 Máy hỏng từ 4 lần trở lên")
        report = df_all.groupby('MÃ_MÁY').agg(
            Lượt_hỏng=('LÝ_DO', 'count'),
            Bệnh_nền=('LÝ_DO', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa bệnh")
        ).reset_index()
        st.dataframe(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False), use_container_width=True)
else:
    st.warning("⚠️ Dữ liệu không hiển thị. Sếp hãy kiểm tra xem Google Sheets đã được 'Xuất bản' đúng chưa.")
