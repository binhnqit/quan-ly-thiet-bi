import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị V71", layout="wide")

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v71():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu thô
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # Dò cột tự động
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(50)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['MÃ', '3534', '1102']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA']) or df_raw.columns[3]
        c_ng = find_col(['/', '202', 'NGÀY']) or df_raw.columns[0]
        c_kh = find_col(['QUANG TRUNG', 'SƠN HẢI', 'KHÁCH']) or df_raw.columns[2]

        # Tạo DataFrame sạch
        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LINH_KIỆN_HƯ'] = df_raw[c_ly].astype(str).str.strip()
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # --- XỬ LÝ NGÀY THÁNG CỰC ĐOAN (FIX FILTER) ---
        # Thử ép kiểu ngày tháng theo chuẩn VN (Ngày/Tháng/Năm)
        df['NGÀY_DT'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        
        # Lấy Năm và Tháng để lọc
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY_DT'].dt.month.fillna(1).astype(int)
        
        # Phân loại vùng miền tự động (Fix biểu đồ tròn)
        def set_region(kh):
            v = str(kh).upper()
            if any(x in v for x in ['BẮC', 'HN', 'PHÚ']): return 'MIỀN BẮC'
            if any(x in v for x in ['TRUNG', 'ĐÀ NẴNG', 'HUẾ']): return 'MIỀN TRUNG'
            return 'MIỀN NAM'
        df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(set_region)

        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR BỘ LỌC ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ HỆ THỐNG")
    if st.button('🚀 ĐỒNG BỘ DỮ LIỆU MỚI'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v71()
    if data is not None:
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Năm báo cáo", y_list, index=y_list.index(2026) if 2026 in y_list else 0)
        
        m_list = [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Tháng báo cáo", m_list, index=0)
        
        # --- LOGIC LỌC CHUẨN ---
        month_int = int(sel_month.replace("Tháng ", ""))
        df_filtered = data[(data['NĂM'] == sel_year) & (data['THÁNG_NUM'] == month_int)]
        
        st.success(f"✅ Đã kết nối {len(df_filtered)} dòng")
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH (5 TAB) ---
st.markdown(f'<h1 style="text-align:center; color:#1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA {sel_year}</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # 1. Chỉ số KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    heavy = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng nặng (>2 lần)", len(heavy[heavy > 2]))
    c4.metric("Khách hàng/Đơn vị", df_filtered['KHÁCH_HÀNG'].nunique())

    # 2. Tabs
    t1, t2, t3, t4, t5 = st.tabs(["📊 BÁO CÁO", "🔍 TRA CỨU", "🚩 DANH SÁCH ĐEN", "🤖 AI ASSISTANT", "📖 HƯỚNG DẪN"])

    with t1:
        st.subheader(f"🛠️ Linh kiện lỗi nhiều nhất {sel_month}")
        chart_data = df_filtered[df_filtered['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
        st.bar_chart(chart_data)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            fig = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.subheader("📋 Top Khách hàng")
            st.dataframe(df_filtered['KHÁCH_HÀNG'].value_counts().head(10), use_container_width=True)

    with t2:
        search = st.text_input(f"Nhập mã máy cần tra cứu trong {sel_month}:")
        if search:
            res = df_filtered[df_filtered['MÃ_MÁY'].str.contains(search, na=False, case=False)]
            st.dataframe(res, use_container_width=True)

    with t3:
        st.subheader("🚩 Thiết bị cần thay mới (Hỏng > 2 lần)")
        st.dataframe(heavy[heavy > 2].reset_index().rename(columns={'count':'Lần hỏng'}), use_container_width=True)

    with t4:
        st.subheader("🤖 Trợ lý AI (Cấp quyền truy cập dữ liệu)")
        user_ask = st.chat_input("Hỏi tôi về dữ liệu tháng này...")
        if user_ask:
            st.write(f"💬 **Câu hỏi:** {user_ask}")
            # Logic xử lý câu hỏi đơn giản
            if "hỏng nhất" in user_ask.lower():
                top = df_filtered['LINH_KIỆN_HƯ'].value_counts().idxmax()
                st.info(f"🤖 Trả lời: Trong {sel_month}, linh kiện **{top}** đang hỏng nhiều nhất sếp ạ.")
            else:
                st.info("🤖 Tôi đang phân tích bảng tính, sếp chờ 1 chút nhé!")

    with t5:
        st.info("Hệ thống V71 đã được tối ưu filter. Nếu số liệu vẫn sai, sếp hãy kiểm tra lại định dạng ngày ở cột A trong file Google Sheets.")

else:
    st.warning(f"⚠️ Không có dữ liệu cho {sel_month}/{sel_year}. Sếp chọn tháng khác nhé!")
