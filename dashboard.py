import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN CHUẨN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V25", layout="wide")

# 2. SỬ DỤNG ID FILE ĐỂ ÉP ĐỌC DỮ LIỆU MỚI NHẤT
# Tôi lấy ID từ chính hình ảnh image_b3b445.png sếp gửi
FILE_ID = "1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv"

@st.cache_data(ttl=2) # Ép làm mới cực nhanh mỗi 2 giây
def load_data_v25():
    try:
        # Thêm tham số ngẫu nhiên để Google không trả về bản cũ (Anti-cache)
        url = f"{SHEET_URL}&cache_bust={pd.Timestamp.now().timestamp()}"
        raw_df = pd.read_csv(url, dtype=str)
        
        df = pd.DataFrame()
        # Ép tọa độ cột từ file thực tế: Cột B (Mã Máy), D (Lý do), G (Ngày)
        df['MÃ_MÁY'] = raw_df.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = raw_df.iloc[:, 3].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce', dayfirst=True)
        
        # Nhận diện vùng miền chuẩn xác
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
        st.error(f"Lỗi kết nối trực tiếp: {e}")
        return pd.DataFrame()

df_all = load_data_v25()

# --- SIDEBAR (Hình image_a8e9e4.png) ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if st.button('🔄 ÉP LÀM MỚI 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        # Mặc định chọn năm mới nhất hoặc 2026
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0)
        list_vung = sorted(df_all['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        df_filtered = df_all[(df_all['NĂM'] == sel_year) & (df_all['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    tab1, tab2, tab4 = st.tabs(["📊 Dashboard", "💬 Chatbot AI", "🚩 Máy Nguy Kịch"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        bad_counts = df_all['MÃ_MÁY'].value_counts()
        crit_list = bad_counts[bad_counts >= 4].index.tolist()
        c3.metric("Máy cần thanh lý", f"{len(crit_list)}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Phân bổ theo Miền")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê linh kiện")
            # Sửa triệt để lỗi bị dồn vào cột "Khác"
            def classify_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'main' in x: return 'Mainboard'
                if 'sạc' in x or 'adapter' in x: return 'Sạc/Adapter'
                if 'ssd' in x or 'ổ' in x: return 'Ổ cứng'
                return 'Linh kiện khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Tra cứu hồ sơ máy")
        q = st.text_input("Gõ mã máy (VD: 3534):")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)].sort_values('NGAY_FIX', ascending=False)
            if not res.empty:
                st.success(f"Dữ liệu Live: Máy {q} đã sửa {len(res)} lần.")
                st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']], use_container_width=True)

    with tab4:
        st.header("🚩 Danh sách đen (Hỏng >= 4 lần)")
        report = df_all.groupby('MÃ_MÁY').agg(
            Lượt_hỏng=('LÝ_DO', 'count'),
            Bệnh_nền=('LÝ_DO', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa bệnh"),
            Khu_vực=('VÙNG_MIỀN', 'first')
        ).reset_index()
        st.dataframe(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Hệ thống đang quét 3.651 dòng... Sếp đợi 3 giây nhé!")
