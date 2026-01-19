import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Quản Trị Tài Sản AI - V40", layout="wide")

# 2. LINK CSV CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v40():
    try:
        sync_url = f"{DATA_URL}&cache_buster={time.time()}"
        df_raw = pd.read_csv(sync_url, on_bad_lines='skip', dtype=str)
        
        if df_raw.empty: return None

        # Làm sạch tên cột (bỏ khoảng trắng thừa)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]

        df = pd.DataFrame()
        # Lấy dữ liệu theo vị trí cột để tránh sai tên
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Không xác định")
        
        # XỬ LÝ NGÀY THÁNG CỰC MẠNH
        raw_dates = df_raw.iloc[:, 6]
        df['NGAY_FIX'] = pd.to_datetime(raw_dates, dayfirst=True, errors='coerce')
        
        # Tạo cột Năm và xử lý dòng lỗi ngày
        df['NĂM'] = df['NGAY_FIX'].dt.year.fillna(0).astype(int)
        df['NĂM_STR'] = df['NĂM'].apply(lambda x: str(x) if x != 0 else "Chưa phân loại")

        # Nhận diện vùng miền
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG", "HCM"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        return df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return None

df_all = load_data_v40()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU MỚI'):
        st.cache_data.clear()
        st.rerun()
    
    if df_all is not None:
        st.success(f"✅ Đã kết nối {len(df_all)} dòng")
        # Thêm tùy chọn "Tất cả các năm" để luôn hiện dữ liệu
        years = ["Tất cả"] + sorted([str(y) for y in df_all['NĂM'].unique() if y != 0], reverse=True)
        if "0" in [str(y) for y in df_all['NĂM'].unique()]: years.append("Chưa phân loại")
        
        sel_year = st.selectbox("📅 Chọn Năm Báo Cáo", years)
        
        if sel_year == "Tất cả":
            df_filtered = df_all
        elif sel_year == "Chưa phân loại":
            df_filtered = df_all[df_all['NĂM'] == 0]
        else:
            df_filtered = df_all[df_all['NĂM'] == int(sel_year)]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💬 Trợ Lý AI", "🚩 Cảnh Báo", "📖 Hướng Dẫn"])
    
    with tab1:
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
            def classify(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc/Adapter'
                return 'Linh kiện khác'
            df_filtered['LINH_KIEN'] = df_filtered['LÝ_DO'].apply(classify)
            st.plotly_chart(px.bar(df_filtered['LINH_KIEN'].value_counts().reset_index(), x='count', y='LINH_KIEN', orientation='h', color='LINH_KIEN'), use_container_width=True)

    with tab2:
        st.subheader("💬 Trợ lý AI Tra cứu Lịch sử")
        q = st.text_input("Gõ mã máy (VD: 3534) hoặc lỗi để AI tìm kiếm trong 3.651 dòng:")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False) | 
                         df_all['LÝ_DO'].str.contains(q, na=False, case=False)]
            st.success(f"Tìm thấy {len(res)} kết quả.")
            st.dataframe(res[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Danh sách máy hỏng nhiều (Cần thanh lý)")
        bad_machines = df_all.groupby('MÃ_MÁY').agg(Số_lần_hỏng=('LÝ_DO', 'count'), Khu_vực=('VÙNG_MIỀN', 'first')).reset_index()
        st.table(bad_machines[bad_machines['Số_lần_hỏng'] >= 4].sort_values('Số_lần_hỏng', ascending=False))

    with tab4:
        st.info("📖 HƯỚNG DẪN VẬN HÀNH")
        st.markdown("""
        ### 1. Xem dữ liệu nhanh
        - Mặc định hệ thống hiện **Tất cả** dữ liệu. Sếp có thể dùng bộ lọc bên trái để xem riêng từng năm.
        - Nếu sếp thấy mục **'Chưa phân loại'**, nghĩa là những dòng đó trong Sheets đang bị sai định dạng ngày tháng.
        
        ### 2. Cách dùng Trợ lý AI
        - Sang Tab **'Trợ Lý AI'**, chỉ cần gõ mã máy. Hệ thống sẽ lục lại toàn bộ lịch sử từ trước đến nay của máy đó.
        
        ### 3. Lưu ý về Google Sheets
        - Sếp nên để cột **Ngày sửa** đồng nhất dạng: `Ngày/Tháng/Năm` (VD: 20/01/2026).
        """)
else:
    st.warning("⚠️ Không có dữ liệu để hiển thị. Sếp vui lòng nhấn 'Cập nhật dữ liệu mới' ở Sidebar.")
