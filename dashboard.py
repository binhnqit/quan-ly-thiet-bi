import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản", layout="wide")

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v68():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- DÒ CỘT TỰ ĐỘNG (KHÔNG THAY ĐỔI CẤU TRÚC) ---
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
        
        # --- XỬ LÝ NGÀY THÁNG CỰC KỲ CẨN THẬN ---
        # Thử nhiều định dạng để không mất dòng dữ liệu nào
        df['NGÀY_TAM'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        # Nếu dòng nào lỗi ngày, gán tạm vào năm 2026 để sếp không bị mất dữ liệu tổng
        df['NĂM'] = df['NGÀY_TAM'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY_TAM'].dt.month.fillna(1).astype(int)
        df['THÁNG'] = df['THÁNG_NUM'].apply(lambda x: f"Tháng {x}")

        # PHÂN LOẠI MIỀN
        def phan_loai(v_mien, k_hang):
            text = (str(v_mien) + " " + str(k_hang)).upper()
            if 'BẮC' in text: return 'MIỀN BẮC'
            if 'TRUNG' in text: return 'MIỀN TRUNG'
            return 'MIỀN NAM'

        vm_col_data = df_raw[c_vm] if c_vm else [""] * len(df)
        df['VÙNG_MIỀN'] = [phan_loai(vm, kh) for vm, kh in zip(vm_col_data, df['KHÁCH_HÀNG'])]
        
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN")
    if st.button('🚀 CẬP NHẬT DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v68()
    if data is not None:
        # LỌC NĂM: Mặc định 2026
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", y_list, index=y_list.index(2026) if 2026 in y_list else 0)
        
        # LỌC THÁNG: Mặc định Tháng 1
        m_list = [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", m_list, index=0)
        
        # THỰC THI LỌC
        df_filtered = data[(data['NĂM'] == sel_year) & (data['THÁNG'] == sel_month)]
        st.success(f"✅ Đã kết nối {len(df_filtered)} dòng")
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN ---
st.markdown(f'<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA {sel_year}</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    st.info(f"📂 Dữ liệu đang hiển thị: **{sel_month} / Năm {sel_year}**")
    
    # 3 CHỈ SỐ CƠ BẢN
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Số thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    heavy = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng nặng (>2 lần)", len(heavy[heavy > 2]))

    # TABS CHỨC NĂNG
    tab1, tab2 = st.tabs(["📊 BIỂU ĐỒ & THỐNG KÊ", "🔍 TRUY LỤC CHI TIẾT"])

    with tab1:
        st.subheader(f"🛠️ Thống kê linh kiện lỗi {sel_month}")
        top_err = df_filtered[df_filtered['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
        st.bar_chart(top_err)
        
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            fig = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with col_r:
            st.subheader("📋 Danh sách linh kiện hư")
            st.dataframe(df_filtered['LINH_KIỆN_HƯ'].value_counts().reset_index(), use_container_width=True)

    with tab2:
        q = st.text_input(f"Tìm mã máy trong {sel_month}:")
        if q:
            res = df_filtered[df_filtered['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN_HƯ', 'VÙNG_MIỀN']], use_container_width=True)
else:
    st.warning(f"⚠️ Không tìm thấy dữ liệu cho {sel_month}/{sel_year}. Sếp hãy kiểm tra lại file nguồn hoặc chọn tháng khác.")
