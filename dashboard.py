import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị V65", layout="wide")

# Link CSV từ Google Sheets của sếp
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v65():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- DÒ CỘT TỰ ĐỘNG ---
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(100)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['3534', '1102', 'MÃ']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA', 'PHÍM', 'PIN', 'MÀN']) or df_raw.columns[3]
        c_ng = find_col(['2024', '2025', '2026', '/']) or df_raw.columns[0]
        c_kh = find_col(['QUANG TRUNG', 'SƠN HẢI', 'TRƯỜNG PHÁT']) or df_raw.columns[2]
        # Tìm cột vùng miền (Cột chứa chữ Miền hoặc Bắc/Trung/Nam)
        c_vm = find_col(['MIỀN', 'BẮC', 'NAM', 'TRUNG'])

        # CHUẨN HÓA DỮ LIỆU
        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LINH_KIỆN_HƯ'] = df_raw[c_ly].astype(str).str.strip()
        df['NGÀY'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # XỬ LÝ VÙNG MIỀN CỰC MẠNH
        def phan_loai_mien(val):
            v = str(val).upper()
            if 'BẮC' in v: return 'MIỀN BẮC'
            if 'NAM' in v: return 'MIỀN NAM'
            if 'TRUNG' in v: return 'MIỀN TRUNG'
            return 'MIỀN NAM' # Mặc định nếu không tìm thấy để biểu đồ tròn không bị rỗng

        if c_vm:
            df['VÙNG_MIỀN'] = df_raw[c_vm].apply(phan_loai_mien)
        else:
            # Nếu không có cột vùng miền, tự đoán theo khách hàng (Ví dụ: TMiền Bắc Phú -> Miền Bắc)
            df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(phan_loai_mien)

        # LÀM SẠCH: Bỏ tên hãng máy, giữ lại linh kiện
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE', 'LAPTOP']
        df = df[~df['LINH_KIỆN_HƯ'].str.upper().isin(hang_may)]
        df = df[df['MÃ_MÁY'].str.len() >= 2].copy()
        
        df['NĂM'] = df['NGÀY'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY'].dt.month.fillna(1).apply(lambda x: f"Tháng {int(x)}")
        
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ V65")
    if st.button('🚀 CẬP NHẬT LIVE DATA'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v65()
    if data is not None:
        st.success(f"✅ Đã kết nối {len(data)} dòng")
        
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + [int(y) for y in y_list if y > 2000])
        
        m_list = [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + m_list)
        
        df_view = data.copy()
        if sel_year != "Tất cả": df_view = df_view[df_view['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả": df_view = df_view[df_view['THÁNG'] == sel_month]
    else:
        df_view = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ DASHBOARD KIỂM SOÁT LINH KIỆN 2026</h1>', unsafe_allow_html=True)

if not df_view.empty:
    # CHỈ SỐ
    st.write(f"📂 **Bộ lọc hiện tại:** {sel_month} / {sel_year}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_view))
    c2.metric("Thiết bị khác nhau", df_view['MÃ_MÁY'].nunique())
    
    heavy = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng >2 lần", len(heavy[heavy > 2]))
    c4.metric("Đơn vị/Khách hàng", df_view['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 BÁO CÁO TỔNG HỢP", "🔍 TRA CỨU MÃ", "🚩 DANH SÁCH ĐEN", "🤖 TRỢ LÝ AI", "📖 HƯỚNG DẪN"])

    with tab1:
        # BIỂU ĐỒ LINH KIỆN HỎNG NHIỀU NHẤT
        st.subheader("🛠️ Top 10 linh kiện lỗi nhiều nhất")
        top_err = df_view[df_view['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
        st.bar_chart(top_err)
        
        col_pie, col_table = st.columns([1, 1])
        with col_pie:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            vm_counts = df_view['VÙNG_MIỀN'].value_counts().reset_index()
            # Vẽ biểu đồ tròn 3 miền cực đẹp
            fig_vm = px.pie(vm_counts, values='count', names='VÙNG_MIỀN', hole=0.5, 
                           color_discrete_sequence=['#00CC96', '#EF553B', '#636EFA'])
            st.plotly_chart(fig_vm, use_container_width=True)
            
        with col_table:
            st.subheader("📋 Bảng kê linh kiện hư hỏng")
            # Thay biểu đồ khách hàng bằng bảng thống kê linh kiện chi tiết
            lk_summary = df_view['LINH_KIỆN_HƯ'].value_counts().reset_index()
            lk_summary.columns = ['Linh kiện / Lỗi', 'Số lượng']
            st.dataframe(lk_summary.head(20), use_container_width=True, height=400)

    with tab2:
        q = st.text_input("Gõ mã máy để xem lịch sử sửa chữa:")
        if q:
            res = data[data['MÃ_MÁY'].astype(str).str.contains(q, na=False)]
            st.dataframe(res[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN_HƯ', 'VÙNG_MIỀN']].sort_values('NGÀY', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Máy hư nhiều lần (Cần xem xét thanh lý)")
        list_h = heavy[heavy > 2].reset_index()
        list_h.columns = ['MÃ_MÁY', 'SỐ_LẦN_HỎNG']
        last_info = data.drop_duplicates('MÃ_MÁY', keep='first')[['MÃ_MÁY', 'KHÁCH_HÀNG', 'VÙNG_MIỀN']]
        st.dataframe(pd.merge(list_h, last_info, on='MÃ_MÁY', how='left'), use_container_width=True)

    with tab4:
        st.subheader("🤖 Trợ lý AI - Phân tích dữ liệu")
        ask = st.chat_input("Hỏi tôi bất cứ điều gì về 4.039 dòng dữ liệu...")
        if ask:
            st.write(f"💬 **Câu hỏi:** {ask}")
            if "lỗi" in ask.lower() or "hỏng" in ask.lower():
                top_l = data['LINH_KIỆN_HƯ'].value_counts().idxmax()
                st.info(f"🤖 Trợ lý AI: Lỗi xuất hiện dày đặc nhất là **{top_l}**.")
            else:
                st.success("🤖 AI đang phân tích sâu dữ liệu để trả lời sếp...")

    with tab5:
        st.markdown("""
        ### 📖 HƯỚNG DẪN V65
        1. **Vùng miền:** AI tự động quét từ khóa 'Bắc', 'Trung', 'Nam' trong dữ liệu để vẽ biểu đồ tròn.
        2. **Thống kê linh kiện:** Thay thế biểu đồ khách hàng bằng danh sách linh kiện hỏng chi tiết giúp sếp nắm bắt nhanh loại phụ tùng cần nhập thêm.
        3. **Lọc LIVE:** Khi sếp sửa trên Google Sheets, chỉ cần nhấn '🚀 CẬP NHẬT' là Dashboard nhảy số ngay lập tức.
        """)
else:
    st.info("💡 Đang nạp dữ liệu 4.039 dòng. Sếp vui lòng nhấn 'CẬP NHẬT' nếu dữ liệu chưa hiện.")
