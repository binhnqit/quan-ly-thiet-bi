import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V26", layout="wide")

# 2. LINK PUBLISH CHUẨN TỪ HÌNH image_b3b445.png CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=10) # Giữ cache 10 giây để tránh overload nhưng vẫn cập nhật nhanh
def load_data_v26():
    try:
        # Thêm biến t để Google không trả về bản cũ
        final_url = f"{DATA_URL}&timestamp={pd.Timestamp.now().timestamp()}"
        # Đọc dữ liệu thô
        raw_df = pd.read_csv(final_url, dtype=str)
        
        # Kiểm tra nếu file có dữ liệu
        if raw_df.empty:
            return pd.DataFrame()

        df = pd.DataFrame()
        # Ép tọa độ cột: B (Mã Máy), D (Lý do), G (Ngày sửa)
        df['MÃ_MÁY'] = raw_df.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = raw_df.iloc[:, 3].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce', dayfirst=True)
        
        # Nhận diện vùng miền (Sửa lỗi dồn vào 'Khác' ở hình image_a943d9.png)
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
        st.error(f"Lỗi đọc dữ liệu: {e}")
        return pd.DataFrame()

df_all = load_data_v26()

# --- SIDEBAR (Hình image_a8e9e4.png) ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if st.button('🔄 LÀM MỚI 3.651 DÒNG'):
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
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        bad_counts = df_all['MÃ_MÁY'].value_counts()
        crit_count = len(bad_counts[bad_counts >= 4])
        c3.metric("Máy cần thay thế", f"{crit_count}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Tỷ lệ hỏng theo Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê linh kiện hỏng")
            def classify_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x or 'adapter' in x: return 'Sạc/Adapter'
                if 'main' in x: return 'Mainboard'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Tra cứu hồ sơ 3.651 dòng")
        q = st.text_input("Gõ mã máy (VD: 3534):")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)]
            if not res.empty:
                st.success(f"Tìm thấy {len(res)} bản ghi cho máy {q}")
                st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.header("🚩 Máy hỏng từ 4 lần trở lên")
        report = df_all.groupby('MÃ_MÁY').agg(
            Lượt_hỏng=('LÝ_DO', 'count'),
            Bệnh_nền=('LÝ_DO', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa bệnh")
        ).reset_index()
        st.dataframe(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False), use_container_width=True)
else:
    st.info("Đang đồng bộ dữ liệu... Sếp hãy kiểm tra xem đã nhấn 'Dừng xuất bản' rồi 'Xuất bản lại' trên Sheets chưa nhé.")
