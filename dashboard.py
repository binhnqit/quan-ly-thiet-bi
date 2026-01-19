import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V29", layout="wide")

# 2. LINK DỮ LIỆU CHUẨN SẾP VỪA GỬI
# Google tự đổi hiển thị nhưng link CSV này vẫn tồn tại vĩnh viễn
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=2) # Làm mới cực nhanh để sếp thấy dữ liệu ngay
def load_data_v29():
    try:
        # Ép Google trả về bản mới nhất bằng cách thêm mã thời gian
        clean_url = f"{DATA_URL}&cache_bust={pd.Timestamp.now().timestamp()}"
        raw_df = pd.read_csv(clean_url, dtype=str)
        
        if raw_df.empty: return pd.DataFrame()

        df = pd.DataFrame()
        # Ánh xạ cột dựa trên file 3.651 dòng của sếp
        df['MÃ_MÁY'] = raw_df.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = raw_df.iloc[:, 3].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce', dayfirst=True)
        
        # Nhận diện vùng miền (Sửa lỗi hình image_a943d9.png)
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = raw_df.apply(detect_vung, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except Exception as e:
        st.error(f"⚠️ Hệ thống đang chờ Google Sheets phản hồi. Lỗi: {e}")
        return pd.DataFrame()

df_all = load_data_v29()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN")
        if st.button('🔄 CẬP NHẬT 3.651 DÒNG'):
            st.cache_data.clear()
            st.rerun()
        
        # Lọc theo năm (Hình image_a8e9e4.png)
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]

    t1, t2, t3 = st.tabs(["📊 Dashboard Chiến Lược", "💬 Tra Cứu Máy", "🚩 Danh Sách Đen"])
    
    with t1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng lượt sửa chữa", f"{len(df_filtered)}")
        c2.metric("Số lượng thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        bad_counts = df_all['MÃ_MÁY'].value_counts()
        crit_count = len(bad_counts[bad_counts >= 4])
        c3.metric("Máy hỏng nặng (>4 lần)", f"{crit_count}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Phân bổ theo Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê linh kiện")
            # Tách linh kiện để biểu đồ đa dạng màu sắc
            def classify(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x or 'adapter' in x: return 'Sạc/Adapter'
                if 'main' in x: return 'Mainboard'
                return 'Linh kiện khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify)
            # Dùng biểu đồ cột ngang để dễ đọc (Hình image_a943d9.png sẽ hết lỗi)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with t2:
        st.subheader("💬 Tra cứu hồ sơ 3.651 dòng")
        q = st.text_input("Gõ mã máy (VD: 3534):")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)]
            st.success(f"Tìm thấy {len(res)} bản ghi cho máy {q}")
            st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with t3:
        st.header("🚩 Máy cần thanh lý ngay")
        report = df_all.groupby('MÃ_MÁY').agg(
            Số_lần_hỏng=('LÝ_DO', 'count'),
            Bệnh_hay_gặp=('LÝ_DO', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa bệnh")
        ).reset_index()
        st.dataframe(report[report['Số_lần_hỏng'] >= 4].sort_values('Số_lần_hỏng', ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Hệ thống đang đồng bộ dữ liệu từ link CSV sếp cung cấp... Vui lòng đợi trong giây lát.")
