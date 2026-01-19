import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN (Giữ nguyên như sếp yêu cầu)
st.set_page_config(page_title="Hệ Thống Quản Trị Live Data", layout="wide")

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v69():
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
        c_vm = find_col(['MIỀN', 'BẮC', 'NAM', 'TRUNG'])

        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LINH_KIỆN_HƯ'] = df_raw[c_ly].astype(str).str.strip()
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # --- XỬ LÝ NGÀY THÁNG ĐỂ LỌC CHÍNH XÁC ---
        # Ép định dạng Ngày/Tháng/Năm, dòng nào lỗi thì mặc định 01/01/2026 để không mất dữ liệu
        df['NGÀY_TAM'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_TAM'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY_TAM'].dt.month.fillna(1).astype(int)
        df['THÁNG'] = df['THÁNG_NUM'].apply(lambda x: f"Tháng {x}")

        # VÙNG MIỀN
        def phan_loai(v_mien, k_hang):
            text = (str(v_mien) + " " + str(k_hang)).upper()
            if 'BẮC' in text: return 'MIỀN BẮC'
            if 'TRUNG' in text: return 'MIỀN TRUNG'
            return 'MIỀN NAM'

        vm_data = df_raw[c_vm] if c_vm else [""] * len(df)
        df['VÙNG_MIỀN'] = [phan_loai(vm, kh) for vm, kh in zip(vm_data, df['KHÁCH_HÀNG'])]
        
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR: BỘ LỌC ĐÚNG Ý SẾP ---
with st.sidebar:
    st.header("⚙️ BỘ LỌC DỮ LIỆU")
    if st.button('🔄 LÀM MỚI (UPDATE)'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v69()
    if data is not None:
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Năm báo cáo", y_list, index=y_list.index(2026) if 2026 in y_list else 0)
        
        m_list = [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Tháng báo cáo", m_list, index=0) # Mặc định Tháng 1
        
        # --- LỌC DỮ LIỆU ---
        df_filtered = data[(data['NĂM'] == sel_year) & (data['THÁNG'] == sel_month)]
        st.success(f"✅ Đã kết nối {len(df_filtered)} dòng")
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH: KHÔI PHỤC MENU 5 TAB ---
st.markdown(f'<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA {sel_year}</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # HIỂN THỊ CHỈ SỐ THEO BỘ LỌC
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    heavy = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng >2 lần", len(heavy[heavy > 2]))
    c4.metric("Đơn vị yêu cầu", df_filtered['KHÁCH_HÀNG'].nunique())

    # --- KHÔI PHỤC MENU ĐÚNG NHƯ ẢNH image_eb8b54.png ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 BÁO CÁO", "🔍 TRA CỨU", "🚩 DANH SÁCH ĐEN", "🤖 AI ASSISTANT", "📖 HƯỚNG DẪN"])

    with tab1:
        st.subheader(f"🛠️ Thống kê linh kiện lỗi {sel_month}")
        top_err = df_filtered[df_filtered['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
        st.bar_chart(top_err)
        
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            fig = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        with col_r:
            st.subheader("📋 Bảng kê linh kiện hỏng")
            st.dataframe(df_filtered['LINH_KIỆN_HƯ'].value_counts().reset_index(), use_container_width=True)

    with tab2:
        q = st.text_input(f"Tra cứu mã máy trong {sel_month}:")
        if q:
            res = df_filtered[df_filtered['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN_HƯ', 'VÙNG_MIỀN']], use_container_width=True)

    with tab3:
        st.subheader("🚩 Danh sách máy hỏng nặng")
        list_h = heavy[heavy > 2].reset_index()
        list_h.columns = ['MÃ_MÁY', 'SỐ_LẦN_HỎNG']
        st.dataframe(list_h, use_container_width=True)

    with tab4:
        st.subheader("🤖 Trợ lý AI")
        st.info(f"AI đang phân tích dữ liệu của {sel_month}/{sel_year}...")
        ask = st.chat_input("Hỏi AI về tình hình hư hỏng...")
        if ask: st.write(f"💬 Câu hỏi: {ask}")

    with tab5:
        st.markdown("### 📖 Hướng dẫn sử dụng hệ thống V69")
        st.write("- Chọn Năm và Tháng ở Sidebar để xem báo cáo chính xác.")
        st.write("- Sử dụng Tab Tra cứu để tìm nhanh lịch sử máy.")

else:
    st.warning(f"⚠️ Không có dữ liệu cho {sel_month}/{sel_year}. Vui lòng kiểm tra lại file nguồn.")
