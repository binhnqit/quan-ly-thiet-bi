import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V42", layout="wide")

# 2. LINK CSV CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v42():
    try:
        sync_url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(sync_url, on_bad_lines='skip', dtype=str)
        if df_raw.empty: return None

        df = pd.DataFrame()
        # Lấy cột 1 (Mã máy), 3 (Lý do), 6 (Ngày sửa)
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Không rõ")
        
        # XỬ LÝ THỜI GIAN CHI TIẾT
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGAY_FIX'].dt.year.fillna(0).astype(int)
        df['THÁNG_SO'] = df['NGAY_FIX'].dt.month.fillna(0).astype(int)
        
        # Tạo tên tháng tiếng Việt
        month_map = {0: "Chưa rõ", 1: "Tháng 1", 2: "Tháng 2", 3: "Tháng 3", 4: "Tháng 4", 
                     5: "Tháng 5", 6: "Tháng 6", 7: "Tháng 7", 8: "Tháng 8", 9: "Tháng 9", 
                     10: "Tháng 10", 11: "Tháng 11", 12: "Tháng 12"}
        df['THÁNG'] = df['THÁNG_SO'].map(month_map)

        # Nhận diện vùng miền
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG", "HCM"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        df['SEARCH_KEY'] = df['MÃ_MÁY'].astype(str) + " " + df['LÝ_DO'].astype(str)
        return df
    except Exception as e:
        return None

df_all = load_data_v42()

# --- SIDEBAR: BỘ LỌC THỜI GIAN ---
with st.sidebar:
    st.header("⚙️ BỘ LỌC DỮ LIỆU")
    if st.button('🔄 LÀM MỚI DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    if df_all is not None:
        st.success(f"✅ Đã kết nối {len(df_all)} dòng")
        
        # 1. Lọc theo Năm
        years = ["Tất cả"] + sorted([str(y) for y in df_all['NĂM'].unique() if y != 0], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", years)
        
        # 2. Lọc theo Tháng (Chỉ hiện các tháng có dữ liệu của năm đó)
        temp_df = df_all if sel_year == "Tất cả" else df_all[df_all['NĂM'] == int(sel_year)]
        months = ["Tất cả"] + sorted(temp_df[temp_df['THÁNG_SO'] != 0]['THÁNG'].unique().tolist(), 
                                     key=lambda x: int(x.split(" ")[1]) if "Tháng" in x else 0)
        sel_month = st.selectbox("📆 Chọn Tháng", months)
        
        # Áp dụng bộ lọc kép
        df_filtered = temp_df
        if sel_month != "Tất cả":
            df_filtered = temp_df[temp_df['THÁNG'] == sel_month]
            
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔍 Trợ Lý Truy Lục", "🚩 Cảnh Báo", "📖 Hướng Dẫn"])
    
    with tab1:
        # Hiển thị tiêu đề lọc để sếp biết mình đang xem gì
        st.write(f"📂 Đang hiển thị: **{sel_month} / {sel_year}**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        counts = df_all['MÃ_MÁY'].value_counts()
        c3.metric("Máy hỏng nặng (>4 lần)", f"{len(counts[counts >= 4])}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', title="Phân bổ Khu vực", hole=0.4), use_container_width=True)
        with cr:
            def get_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(get_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', title="Linh kiện hỏng nhiều"), use_container_width=True)

    with tab2:
        st.subheader("🔍 Trợ Lý Truy Lục Lịch Sử")
        q = st.text_input("Nhập Mã máy hoặc Lỗi để tìm kiếm nhanh:")
        if q:
            res = df_all[df_all['SEARCH_KEY'].str.contains(q, na=False, case=False)]
            st.info(f"Tìm thấy {len(res)} kết quả trong toàn bộ lịch sử.")
            st.dataframe(res[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Máy cần thanh lý (Sửa >= 4 lần)")
        report = df_all.groupby('MÃ_MÁY').agg(Lượt_hỏng=('LÝ_DO', 'count'), Vùng=('VÙNG_MIỀN', 'first')).reset_index()
        st.table(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False))

    with tab4:
        st.info("📖 HƯỚNG DẪN BỘ LỌC")
        st.markdown(f"""
        - **Lọc Năm:** Chọn năm sếp muốn xem tại Sidebar.
        - **Lọc Tháng:** Sau khi chọn năm, danh sách tháng sẽ tự động cập nhật những tháng có dữ liệu.
        - **Tất cả:** Chọn 'Tất cả' ở cả 2 mục để xem tổng quát **{len(df_all)}** dòng dữ liệu.
        """)
else:
    st.warning("⚠️ Không có dữ liệu cho thời gian đã chọn. Sếp thử chọn tháng khác hoặc nhấn 'Làm mới' nhé!")
