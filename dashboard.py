import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V38", layout="wide")

# 2. LINK CSV SẾP CUNG CẤP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v38():
    try:
        # Cơ chế chống nghẽn cache
        sync_url = f"{DATA_URL}&nocache={time.time()}"
        df_raw = pd.read_csv(sync_url, on_bad_lines='skip', dtype=str)
        
        if df_raw.empty: return None

        df = pd.DataFrame()
        # Ánh xạ cột (Cột 1: Mã máy, 3: Lý do, 6: Ngày sửa)
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Chưa rõ")
        
        # Sửa lỗi nhận diện ngày tháng để fix lỗi "0 dòng"
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], dayfirst=True, errors='coerce')
        
        # Nhận diện vùng miền
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        
        # Loại bỏ các dòng không có ngày hợp lệ
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year.astype(int)
        return df
    except Exception as e:
        return None

df_all = load_data_v38()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    if df_all is not None:
        st.success(f"✅ Đã kết nối {len(df_all)} dòng")
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm Báo Cáo", list_years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]
    else:
        st.error("❌ Lỗi kết nối CSV")
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # KHÔI PHỤC ĐẦY ĐỦ 4 TAB
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💬 Trợ Lý AI", "🚩 Cảnh Báo", "📖 Hướng Dẫn"])
    
    with tab1:
        # Hiển thị số liệu như hình image_b4a40a.png
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
            def get_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(get_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Trợ lý AI Tra cứu Lịch sử")
        q = st.text_input("Gõ mã máy (VD: 3534) hoặc tên lỗi để AI truy lục:")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False) | 
                         df_all['LÝ_DO'].str.contains(q, na=False, case=False)]
            st.write(f"🔍 AI tìm thấy {len(res)} lịch sử liên quan:")
            st.dataframe(res[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Danh sách máy cần thanh lý")
        report = df_all.groupby('MÃ_MÁY').agg(Lượt_hỏng=('LÝ_DO', 'count'), Vùng=('VÙNG_MIỀN', 'first')).reset_index()
        st.table(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False))

    with tab4:
        st.info("📖 HƯỚNG DẪN VẬN HÀNH CHO SẾP")
        st.markdown("""
        1. **Đồng bộ dữ liệu:** Nhấn nút **'CẬP NHẬT DỮ LIỆU'** ở sidebar khi sếp vừa sửa Google Sheets.
        2. **Sử dụng Trợ lý AI:** Vào Tab **'Trợ Lý AI'**, gõ mã máy để biết lịch sử "bệnh tình". Nếu máy hỏng cùng 1 lỗi nhiều lần, hãy kiểm tra kỹ chất lượng sửa chữa.
        3. **Duyệt thanh lý:** Tab **'Cảnh Báo'** liệt kê những máy hỏng trên 4 lần. Sếp nên ký duyệt mua máy mới thay vì sửa tiếp để tối ưu ngân sách.
        4. **Lọc thời gian:** Dùng menu chọn Năm ở bên trái để xem báo cáo quá khứ hoặc hiện tại.
        """)
else:
    st.warning("⚠️ Đang xử lý dữ liệu. Nếu thấy hiện số 0, sếp hãy nhấn nút 'Cập nhật dữ liệu' ở Sidebar.")
