import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V34", layout="wide")

# 2. LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_final():
    try:
        # Thêm tham số ngẫu nhiên để ép Google nhả dữ liệu mới nhất (Fix lỗi b4bf4f)
        bug_buster_url = f"{DATA_URL}&nocache={time.time()}"
        df_raw = pd.read_csv(bug_buster_url, dtype=str)
        
        if df_raw.empty: return pd.DataFrame()

        df = pd.DataFrame()
        # Ánh xạ cột dựa trên thực tế 3.651 dòng của sếp
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Không xác định")
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], errors='coerce', dayfirst=True)
        
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame()

df_all = load_data_final()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ")
        if st.button('🔄 LÀM MỚI HỆ THỐNG'):
            st.cache_data.clear()
            st.rerun()
        
        years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]

    # KHÔI PHỤC CÁC TAB CHỨC NĂNG
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💬 Trợ Lý AI", "🚩 Máy Nguy Kịch", "📖 Hướng Dẫn"])
    
    with tab1:
        # Hiển thị các con số như hình image_b4a40a.png
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        counts = df_all['MÃ_MÁY'].value_counts()
        c3.metric("Máy hỏng nặng", f"{len(counts[counts >= 4])}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Tỷ lệ theo Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê Linh kiện")
            def classify(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc/Adapter'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Trợ lý AI Tra cứu Lịch sử")
        search = st.text_input("Nhập mã máy (VD: 3534) hoặc tên lỗi:")
        if search:
            res = df_all[df_all['MÃ_MÁY'].str.contains(search, na=False, case=False) | 
                         df_all['LÝ_DO'].str.contains(search, na=False, case=False)]
            st.dataframe(res.sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Danh sách máy hỏng >= 4 lần")
        report = df_all.groupby('MÃ_MÁY').agg(Lượt_hỏng=('LÝ_DO', 'count'), Khu_vực=('VÙNG_MIỀN', 'first')).reset_index()
        st.table(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False))

    with tab4:
        st.info("📖 HƯỚNG DẪN VẬN HÀNH")
        st.markdown("""
        * **Bước 1:** Nhập liệu vào Google Sheets.
        * **Bước 2:** Quay lại đây nhấn nút **'LÀM MỚI HỆ THỐNG'**.
        * **Bước 3:** Sử dụng **Trợ lý AI** để kiểm tra lịch sử sửa chữa của từng máy trước khi duyệt chi.
        """)
else:
    st.warning("⚠️ Đang chờ dữ liệu từ Google Sheets. Nếu sếp vừa cập nhật, hãy đợi 10 giây rồi nhấn 'Làm mới'.")
