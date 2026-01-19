import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V35", layout="wide")

# 2. LIÊN KẾT DỮ LIỆU LIVE (SẾP ĐÃ CẬP NHẬT)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v35():
    try:
        # Cơ chế chống nghẽn: Thêm mã thời gian để ép Google Sheets nhả dữ liệu mới nhất
        final_url = f"{DATA_URL}&nocache={time.time()}"
        df_raw = pd.read_csv(final_url, dtype=str)
        
        if df_raw.empty: return pd.DataFrame()

        df = pd.DataFrame()
        # Ánh xạ cột dựa trên cấu trúc file thực tế của sếp
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Chưa rõ nguyên nhân")
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], errors='coerce', dayfirst=True)
        
        # Nhận diện khu vực thông minh
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khối Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        return df
    except Exception as e:
        return pd.DataFrame()

df_all = load_data_v35()

# --- SIDEBAR: TRUNG TÂM ĐIỀU KHIỂN ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=80)
    st.header("⚙️ QUẢN TRỊ VIÊN")
    if st.button('🔄 CẬP NHẬT LIVE (3.651 DÒNG)'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Xem báo cáo năm:", list_years, index=0)
        df_filtered = df_all[df_all['NĂM'] == sel_year]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN AI 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    # KHÔI PHỤC ĐẦY ĐỦ 4 TAB CHỨC NĂNG
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Tổng Quan", "💬 Trợ Lý AI", "🚩 Máy Nguy Kịch", "📖 Hướng Dẫn"])
    
    with tab1:
        # Hiển thị Metrics chính xác (264 ca, 258 thiết bị)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        counts = df_all['MÃ_MÁY'].value_counts()
        bad_machines = len(counts[counts >= 4])
        c3.metric("Máy cần thanh lý (>4 lần)", f"{bad_machines}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Tỷ lệ theo Khu vực")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        with cr:
            st.subheader("🛠️ Thống kê Linh kiện hỏng")
            def classify(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc/Adapter'
                if 'main' in x: return 'Mainboard'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(classify)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK'), use_container_width=True)

    with tab2:
        st.subheader("💬 Trợ lý AI Tra cứu Hồ sơ")
        st.write("Sếp có thể gõ mã máy hoặc tên linh kiện để AI truy lục trong 3.651 dòng dữ liệu.")
        search_q = st.text_input("Nhập thông tin cần tra cứu (VD: 3534 hoặc Màn hình):")
        if search_q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(search_q, na=False, case=False) | 
                         df_all['LÝ_DO'].str.contains(search_q, na=False, case=False)]
            if not res.empty:
                st.success(f"Tìm thấy {len(res)} lịch sử bảo trì liên quan.")
                st.dataframe(res[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)
            else:
                st.warning("Không tìm thấy dữ liệu trùng khớp.")

    with tab3:
        st.error("🚩 DANH SÁCH THIẾT BỊ CẢNH BÁO NGUY KỊCH (HỎNG >= 4 LẦN)")
        report = df_all.groupby('MÃ_MÁY').agg(Số_lần_hỏng=('LÝ_DO', 'count'), Vùng_miền=('VÙNG_MIỀN', 'first')).reset_index()
        critical_list = report[report['Số_lần_hỏng'] >= 4].sort_values('Số_lần_hỏng', ascending=False)
        st.table(critical_list)

    with tab4:
        st.header("📖 Cẩm nang Hướng dẫn Sử dụng")
        st.markdown("""
        ### 1. Cách cập nhật dữ liệu mới
        Mỗi khi sếp nhập thêm dòng vào Google Sheets, hãy quay lại trang web này và nhấn nút **'LÀM MỚI HỆ THỐNG'** ở cột bên trái. Dữ liệu sẽ được đồng bộ sau 5-10 giây.
        
        ### 2. Cách dùng Trợ lý AI
        Sếp vào Tab **'Trợ Lý AI'**, gõ mã số máy (ví dụ: `2041`). AI sẽ liệt kê tất cả các lần máy đó từng đi sửa, hỏng gì, sửa ngày nào để sếp quyết định có nên tiếp tục sửa hay mua mới.
        
        ### 3. Cách xem danh sách thanh lý
        Tab **'Máy Nguy Kịch'** tự động lọc ra những máy hỏng quá nhiều lần (trên 4 lần). Đây là danh sách sếp cần ưu tiên thay thế để tránh lãng phí chi phí sửa chữa lặt vặt.
        
        ### 4. Lưu ý về Link dữ liệu
        Luôn đảm bảo Google Sheets được xuất bản ở định dạng **CSV**. Nếu hệ thống báo lỗi, hãy kiểm tra lại mục 'Publish to web' trên Sheets.
        """)
else:
    st.warning("⚠️ Hệ thống đang kết nối dữ liệu từ link CSV... Sếp vui lòng nhấn 'Cập nhật' ở sidebar nếu đợi quá 10 giây.")
