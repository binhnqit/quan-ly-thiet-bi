import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V23", layout="wide")

# 2. LINK DỮ LIỆU CHUẨN (CẬP NHẬT 3.651 DÒNG)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v23():
    try:
        # Ép kiểu string và thêm cache_bust để cập nhật dữ liệu mới nhất
        raw_df = pd.read_csv(f"{DATA_URL}&cache={pd.Timestamp.now().timestamp()}", dtype=str)
        
        df = pd.DataFrame()
        # Ép tọa độ cột chuẩn: B=Mã Máy, D=Lý do, G=Ngày sửa
        df['MÃ_MÁY'] = raw_df.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = raw_df.iloc[:, 3].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce', dayfirst=True)
        
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"
        
        df['VÙNG_MIỀN'] = raw_df.apply(detect_vung, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df_all = load_data_v23()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU MỚI'):
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
    tab1, tab2, tab4, tab3 = st.tabs(["📊 Dashboard", "💬 Chatbot AI", "🚩 Máy Nguy Kịch", "📖 Hướng Dẫn"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng (Lọc)", f"{len(df_filtered)}")
        c2.metric("Số lượng thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        bad_counts = df_all['MÃ_MÁY'].value_counts()
        crit_list = bad_counts[bad_counts >= 4].index.tolist()
        c3.metric("Tổng máy hỏng nhiều", f"{len(crit_list)}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Phân bổ hỏng theo Miền")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Loại linh kiện thay thế")
            def classify_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'main' in x: return 'Mainboard'
                if 'sạc' in x or 'adapter' in x: return 'Sạc/Adapter'
                return 'Linh kiện khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h'), use_container_width=True)

    with tab2:
        st.subheader("💬 Tra cứu hồ sơ máy (Live)")
        q = st.text_input("Gõ mã máy để AI quét lịch sử:")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)].sort_values('NGAY_FIX', ascending=False)
            if not res.empty:
                st.success(f"Máy {q} đã sửa {len(
