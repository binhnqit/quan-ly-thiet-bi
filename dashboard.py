import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V30", layout="wide")

# 2. DÁN LINK CSV MỚI CỦA SẾP VÀO ĐÂY
# Phải đảm bảo link có đuôi: pub?output=csv
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v30():
    try:
        # Kiểm tra link nhầm định dạng pubhtml
        if "pubhtml" in DATA_URL:
            st.error("❌ Sếp dán nhầm link 'Trang web'. Hãy chọn lại định dạng '.csv' trong Google Sheets!")
            return pd.DataFrame()
            
        final_url = f"{DATA_URL}&t={pd.Timestamp.now().timestamp()}"
        df_raw = pd.read_csv(final_url, dtype=str)
        
        if df_raw.empty: return pd.DataFrame()

        # Xử lý dữ liệu thô (Cột B: Mã máy, D: Lý do, G: Ngày)
        df = pd.DataFrame()
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
    except Exception as e:
        st.warning(f"🔄 Đang kết nối dữ liệu... Nếu đợi quá 10 giây sếp hãy kiểm tra lại link CSV. (Lỗi: {e})")
        return pd.DataFrame()

df_all = load_data_v30()

# --- GIAO DIỆN ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ")
        if st.button('🔄 CẬP NHẬT LIVE'):
            st.cache_data.clear()
            st.rerun()
        
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]

    t1, t2, t3 = st.tabs(["📊 Dashboard", "💬 Tra Cứu", "🚩 Cảnh Báo"])
    
    with t1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Lượt sửa chữa", f"{len(df_filtered)}")
        c2.metric("Thiết bị hỏng", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        counts = df_all['MÃ_MÁY'].value_counts()
        c3.metric("Máy hỏng nặng (>4 lần)", f"{len(counts[counts >= 4])}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Linh kiện")
            def classify(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc'
                return 'Linh kiện khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)
else:
    st.info("💡 Hướng dẫn: Sếp hãy vào Google Sheets -> Xuất bản lên web -> Chọn 'Giá trị phân tách bằng dấu phẩy (.csv)' thay vì 'Trang web'.")
