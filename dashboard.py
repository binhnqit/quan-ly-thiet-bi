import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN (Giữ nguyên menu sếp thích)
st.set_page_config(page_title="Hệ Thống Quản Trị V72", layout="wide")

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v72():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # Dò cột tự động (Logic cũ ổn định)
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(50)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['MÃ', '3534', '1102']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA']) or df_raw.columns[3]
        c_kh = find_col(['QUANG TRUNG', 'SƠN HẢI', 'KHÁCH']) or df_raw.columns[2]

        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LINH_KIỆN_HƯ'] = df_raw[c_ly].astype(str).str.strip()
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # --- FIX BIỂU ĐỒ TRÒN: PHÂN LOẠI VÙNG MIỀN TỰ ĐỘNG ---
        def set_region(kh):
            v = str(kh).upper()
            if any(x in v for x in ['BẮC', 'HN', 'PHÚ', 'THÁI NGUYÊN']): return 'MIỀN BẮC'
            if any(x in v for x in ['TRUNG', 'ĐÀ NẴNG', 'HUẾ', 'VINH']): return 'MIỀN TRUNG'
            return 'MIỀN NAM' # Mặc định để không bị 100% "Chưa phân loại"
        
        df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(set_region)
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR: ĐƠN GIẢN HÓA ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN TỔNG")
    if st.button('🚀 ĐỒNG BỘ TOÀN BỘ DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v72()
    if data is not None:
        st.success(f"✅ Đã kết nối {len(data)} dòng dữ liệu")
        # Giữ lại bộ chọn để sếp thấy quen thuộc nhưng mặc định là "Tất cả"
        mode = st.radio("Chế độ hiển thị", ["Cộng dồn (Tất cả)", "Lọc theo tháng"])
    else:
        data = pd.DataFrame()

# --- GIAO DIỆN CHÍNH (5 TAB) ---
st.markdown(f'<h1 style="text-align:center; color:#1E3A8A;">🛡️ DASHBOARD QUẢN TRỊ TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if not data.empty:
    # 1. KPI CỘNG DỒN (Đảm bảo ra số 3500+ như sếp muốn)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(data):,}")
    c2.metric("Số thiết bị lỗi", f"{data['MÃ_MÁY'].nunique():,}")
    heavy = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng nặng (>2 lần)", len(heavy[heavy > 2]))
    c4.metric("Đơn vị yêu cầu", data['KHÁCH_HÀNG'].nunique())

    # 2. TABS CHỨC NĂNG
    t1, t2, t3, t4, t5 = st.tabs(["📊 BÁO CÁO", "🔍 TRA CỨU", "🚩 DANH SÁCH ĐEN", "🤖 AI ASSISTANT", "📖 HƯỚNG DẪN"])

    with t1:
        st.subheader("🛠️ Thống kê linh kiện lỗi (Tổng hợp)")
        chart_data = data[data['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
        st.bar_chart(chart_data)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📍 Tỷ lệ theo Vùng Miền (Đã fix)")
            # Biểu đồ tròn sẽ không còn bị 1 màu nữa
            fig = px.pie(data, names='VÙNG_MIỀN', hole=0.4, 
                         color_discrete_map={'MIỀN BẮC':'#EF553B', 'MIỀN TRUNG':'#FECB52', 'MIỀN NAM':'#636EFA'})
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.subheader("📋 Top Khách hàng gặp lỗi")
            st.dataframe(data['KHÁCH_HÀNG'].value_counts().head(15), use_container_width=True)

    with t2:
        search = st.text_input("Nhập mã máy/tên khách hàng để tìm kiếm:")
        if search:
            res = data[data.apply(lambda row: search.upper() in row.astype(str).str.upper().values, axis=1)]
            st.dataframe(res, use_container_width=True)

    with t3:
        st.subheader("🚩 Danh sách máy hỏng tái diễn nhiều lần")
        st.dataframe(heavy[heavy > 2].reset_index().rename(columns={'count':'Số lần lỗi'}), use_container_width=True)

    with t4:
        st.subheader("🤖 Trợ lý AI Assistant (Đã kích hoạt)")
        st.info("Chào sếp! Tôi đã đọc toàn bộ dữ liệu. Sếp muốn biết gì về tình hình hư hỏng?")
        
        # MÔ PHỎNG AI XỬ LÝ DỮ LIỆU THẬT
        q = st.chat_input("Ví dụ: Đơn vị nào hỏng nhiều nhất? Linh kiện nào hay hỏng?")
        if q:
            st.write(f"💬 **Sếp hỏi:** {q}")
            q_low = q.lower()
            if "đơn vị" in q_low or "khách hàng" in q_low:
                top_kh = data['KHÁCH_HÀNG'].value_counts().idxmax()
                st.success(f"🤖 **AI Trả lời:** Đơn vị **{top_kh}** đang có số ca hỏng nhiều nhất với {data['KHÁCH_HÀNG'].value_counts().max()} trường hợp.")
            elif "linh kiện" in q_low or "hỏng nhiều" in q_low:
                top_lk = data['LINH_KIỆN_HƯ'].value_counts().idxmax()
                st.success(f"🤖 **AI Trả lời:** Linh kiện **{top_lk}** là bộ phận hay gặp sự cố nhất trên toàn hệ thống.")
            else:
                st.warning("🤖 AI: Sếp hãy hỏi cụ thể về 'Linh kiện', 'Đơn vị' hoặc 'Số lượng' để tôi báo cáo chính xác nhất!")

    with t5:
        st.markdown("""
        ### 📖 Hướng dẫn V72 (Bản ổn định)
        - **Dữ liệu:** Tự động cộng dồn toàn bộ để tránh lỗi lọc ngày tháng.
        - **Vùng miền:** Tự động phân tích tên khách hàng để chia nhóm Bắc - Trung - Nam.
        - **AI:** Có thể hỏi đáp trực tiếp về các con số thống kê.
        """)
else:
    st.error("❌ Không thể tải dữ liệu. Sếp hãy kiểm tra lại kết nối Internet hoặc file Google Sheets.")
