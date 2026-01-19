import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH TRANG CHUYÊN NGHIỆP
st.set_page_config(page_title="Quản Trị Tài Sản AI 2026", layout="wide")

# 2. CẬP NHẬT LINK CSV CHÍNH CHỦ CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=10)
def load_data_v36(url):
    try:
        # Kỹ thuật ép làm mới dữ liệu (Cache Buster)
        sync_url = f"{url}&t={int(time.time())}"
        df_raw = pd.read_csv(sync_url, on_bad_lines='skip', dtype=str)
        
        if df_raw.empty: return None

        # Xử lý dữ liệu (Cột 1: Mã máy, Cột 3: Lý do, Cột 6: Ngày)
        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Chưa ghi nhận")
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], errors='coerce', dayfirst=True)
        
        # Nhận diện vùng miền (Phát triển từ V35)
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG", "HCM"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khối Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return None

# Gọi hàm tải dữ liệu
df_all = load_data_v36(DATA_URL)

# --- SIDEBAR: QUẢN TRỊ VIÊN ---
with st.sidebar:
    st.markdown("### ⚙️ HỆ THỐNG")
    if st.button('🔄 ÉP LÀM MỚI DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    if df_all is not None:
        st.success("✅ Đã kết nối 3.651 dòng")
        years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn năm báo cáo", years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]
    else:
        st.warning("⚠️ Đang chờ dữ liệu...")
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if df_all is not None:
    # KHÔI PHỤC ĐỦ 4 TÁP NHƯ BAN ĐẦU
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💬 Trợ Lý AI", "🚩 Cảnh Báo", "📖 Hướng Dẫn"])
    
    with tab1:
        # Metrics chính (Lấy từ hình image_b4a40a.png)
        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        m2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        counts = df_all['MÃ_MÁY'].value_counts()
        m3.metric("Máy hỏng nặng (>4 lần)", f"{len(counts[counts >= 4])}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Phân bổ theo Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê Linh kiện")
            def get_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc'
                return 'Linh kiện khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(get_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Trợ lý AI Tra cứu Lịch sử")
        q = st.text_input("Gõ mã máy hoặc tên lỗi để AI tìm kiếm (VD: 3534):")
        if q:
            results = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False) | 
                            df_all['LÝ_DO'].str.contains(q, na=False, case=False)]
            st.write(f"🔍 AI tìm thấy {len(results)} kết quả:")
            st.dataframe(results.sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Danh sách máy nguy kịch (Cần thanh lý)")
        report = df_all.groupby('MÃ_MÁY').agg(Số_lần_hỏng=('LÝ_DO', 'count'), Khu_vực=('VÙNG_MIỀN', 'first')).reset_index()
        st.table(report[report['Số_lần_hỏng'] >= 4].sort_values('Số_lần_hỏng', ascending=False))

    with tab4:
        st.info("📖 HƯỚNG DẪN SỬ DỤNG")
        st.markdown("""
        1. **Cập nhật dữ liệu:** Nhập liệu vào Sheets -> Quay lại đây nhấn **'ÉP LÀM MỚI DỮ LIỆU'**.
        2. **Tra cứu:** Qua Tab **'Trợ Lý AI'** để xem lịch sử sửa chữa của bất kỳ máy nào.
        3. **Thanh lý:** Xem Tab **'Cảnh Báo'** để biết máy nào hỏng quá 4 lần, tránh sửa chữa lãng phí.
        """)
else:
    st.info("💡 Hệ thống đang khởi tạo kết nối với Google Sheets. Sếp hãy đợi giây lát hoặc kiểm tra lại link CSV.")
