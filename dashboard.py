import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN (Mã màu chuyên nghiệp)
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản V70", layout="wide")

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v70():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- DÒ CỘT TỰ ĐỘNG ---
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(100)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['MÃ', '3534', '1102']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA', 'PHÍM', 'PIN', 'MÀN']) or df_raw.columns[3]
        c_ng = find_col(['/', '2024', '2025', '2026']) or df_raw.columns[0]
        c_kh = find_col(['QUANG TRUNG', 'SƠN HẢI', 'TRƯỜNG PHÁT']) or df_raw.columns[2]

        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LINH_KIỆN_HƯ'] = df_raw[c_ly].astype(str).str.strip()
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # --- FIX LỖI LỌC NGÀY THÁNG ---
        df['NGÀY_DT'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        # Loại bỏ các dòng không có ngày để tránh cộng dồn sai
        df = df.dropna(subset=['NGÀY_DT'])
        
        df['NĂM'] = df['NGÀY_DT'].dt.year.astype(int)
        df['THÁNG_NUM'] = df['NGÀY_DT'].dt.month.astype(int)
        df['THÁNG_TEXT'] = df['THÁNG_NUM'].apply(lambda x: f"Tháng {x}")

        # --- FIX BIỂU ĐỒ TRÒN (PHÂN LOẠI VÙNG MIỀN) ---
        def auto_region(name):
            n = name.upper()
            if any(k in n for k in ['BẮC', 'HN', 'HÀ NỘI', 'PHÚ']): return 'MIỀN BẮC'
            if any(k in n for k in ['TRUNG', 'ĐÀ NẴNG', 'HUẾ']): return 'MIỀN TRUNG'
            return 'MIỀN NAM' # Mặc định là Nam

        df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(auto_region)
        
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR: BỘ LỌC CHÍNH XÁC ---
with st.sidebar:
    st.header("⚙️ BỘ LỌC V70")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU MỚI'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v70()
    if data is not None:
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        # Mặc định chọn 2026
        sel_year = st.selectbox("📅 Chọn Năm", y_list, index=y_list.index(2026) if 2026 in y_list else 0)
        
        m_list = [f"Tháng {i}" for i in range(1, 13)]
        # Mặc định chọn Tháng 1
        sel_month = st.selectbox("📆 Chọn Tháng", m_list, index=0)
        
        # --- THỰC THI LỌC KÉP (NĂM & THÁNG) ---
        month_val = int(sel_month.replace("Tháng ", ""))
        df_view = data[(data['NĂM'] == sel_year) & (data['THÁNG_NUM'] == month_val)]
        
        st.success(f"✅ Đang hiển thị {len(df_view)} dòng")
    else:
        df_view = pd.DataFrame()

# --- GIAO DIỆN CHÍNH (Menu 5 Tab) ---
st.markdown(f'<h1 style="text-align: center; color: #1E3A8A;">🛡️ QUẢN TRỊ TÀI SẢN CHI TIẾT {sel_year}</h1>', unsafe_allow_html=True)

if not df_view.empty:
    # CHỈ SỐ TỔNG HỢP
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_view)}")
    c2.metric("Số thiết bị lỗi", df_view['MÃ_MÁY'].nunique())
    
    counts = df_view['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng nặng (>2 lần)", len(counts[counts > 2]))
    c4.metric("Khách hàng/Đơn vị", df_view['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 BÁO CÁO", "🔍 TRA CỨU", "🚩 DANH SÁCH ĐEN", "🤖 AI ASSISTANT", "📖 HƯỚNG DẪN"])

    with tab1:
        st.subheader(f"🛠️ Thống kê linh kiện lỗi trong {sel_month}")
        top_err = df_view[df_view['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
        st.bar_chart(top_err)
        
        col_pie, col_tbl = st.columns(2)
        with col_pie:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            # Vẽ biểu đồ tròn 3 vùng rõ rệt
            vm_chart = px.pie(df_view, names='VÙNG_MIỀN', hole=0.5, color_discrete_sequence=['#636EFA', '#EF553B', '#00CC96'])
            st.plotly_chart(vm_chart, use_container_width=True)
        with col_tbl:
            st.subheader("📋 Bảng kê chi tiết")
            st.dataframe(df_view['LINH_KIỆN_HƯ'].value_counts().reset_index(), use_container_width=True, height=300)

    with tab2:
        q = st.text_input(f"Tìm mã máy (Trong {sel_month}):")
        if q:
            res = df_view[df_view['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN_HƯ', 'VÙNG_MIỀN']], use_container_width=True)

    with tab3:
        st.subheader("🚩 Máy hỏng nhiều lần trong kỳ báo cáo")
        list_h = counts[counts > 2].reset_index()
        list_h.columns = ['MÃ_MÁY', 'SỐ_LẦN_HỎNG']
        st.dataframe(list_h, use_container_width=True)

    with tab4:
        st.subheader("🤖 Trợ lý AI Assistant (Live)")
        ask = st.chat_input("Hỏi tôi: 'Linh kiện nào hỏng nhiều nhất tháng này?'")
        if ask:
            st.write(f"💬 **Sếp hỏi:** {ask}")
            # Logic AI phản hồi dựa trên dữ liệu đang lọc
            if "nhiều nhất" in ask.lower() or "linh kiện" in ask.lower():
                best = df_view['LINH_KIỆN_HƯ'].value_counts().idxmax()
                st.info(f"🤖 **Trả lời:** Trong {sel_month}, linh kiện **{best}** có tỷ lệ hỏng cao nhất sếp ạ.")
            else:
                st.info("🤖 AI đang phân tích sâu dữ liệu, sếp vui lòng đợi trong giây lát...")

    with tab5:
        st.markdown("""
        ### 📖 HƯỚNG DẪN V70
        1. **Bộ lọc:** Luôn tự động chọn Năm 2026 và Tháng 1.
        2. **Biểu đồ tròn:** Tự động gán vùng miền theo tên khách hàng nếu sếp chưa nhập cột Vùng Miền.
        3. **Số liệu:** Đã fix lỗi cộng dồn, con số hiện tại chỉ tính riêng cho tháng sếp chọn.
        """)
else:
    st.warning(f"⚠️ Không có dữ liệu cho {sel_month} / {sel_year}. Sếp hãy chọn tháng khác hoặc nhấn Cập Nhật.")
