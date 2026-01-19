import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống Quản Trị V67", layout="wide")

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v67():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
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
        
        # --- XỬ LÝ NGÀY THÁNG QUYẾT ĐỊNH VIỆC LỌC ---
        # Ép định dạng ngày chuẩn Việt Nam (Ngày/Tháng/Năm)
        df['NGÀY_DT'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        
        # Chỉ giữ lại những dòng có ngày tháng hợp lệ
        df = df.dropna(subset=['NGÀY_DT'])
        
        # Tách rõ ràng Năm và Tháng để lọc không bị sai lệch
        df['NĂM_SO_SANH'] = df['NGÀY_DT'].dt.year.astype(int)
        df['THÁNG_SO_SANH'] = df['NGÀY_DT'].dt.month.astype(int)
        
        # Nhãn hiển thị cho bộ lọc
        df['THÁNG_HIEN_THI'] = df['THÁNG_SO_SANH'].apply(lambda x: f"Tháng {x}")

        # VÙNG MIỀN
        def phan_loai_mien(val):
            v = str(val).upper()
            if 'BẮC' in v: return 'MIỀN BẮC'
            if 'TRUNG' in v: return 'MIỀN TRUNG'
            return 'MIỀN NAM'

        if c_vm:
            df['VÙNG_MIỀN'] = df_raw[c_vm].apply(phan_loai_mien)
        else:
            df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(phan_loai_mien)

        # Lọc bỏ linh kiện rác
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE', 'LAPTOP']
        df = df[~df['LINH_KIỆN_HƯ'].str.upper().isin(hang_may)]
        
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR: BỘ LỌC CẢI TIẾN ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN")
    if st.button('🚀 LÀM MỚI DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v67()
    if data is not None:
        # LỌC NĂM: Mặc định 2026
        y_list = sorted(data['NĂM_SO_SANH'].unique(), reverse=True)
        try:
            def_y_idx = y_list.index(2026) + 1
        except:
            def_y_idx = 0
            
        sel_year = st.selectbox("📅 Năm báo cáo", ["Tất cả"] + [int(y) for y in y_list], index=def_y_idx)
        
        # LỌC THÁNG: Mặc định Tháng 1 (Để tránh hiện quá nhiều dữ liệu)
        m_list = [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Tháng báo cáo", ["Tất cả"] + m_list, index=1) # index=1 là Tháng 1
        
        # --- LOGIC LỌC CHÍNH XÁC TUYỆT ĐỐI ---
        df_filtered = data.copy()
        if sel_year != "Tất cả":
            df_filtered = df_filtered[df_filtered['NĂM_SO_SANH'] == int(sel_year)]
        
        if sel_month != "Tất cả":
            # Lấy con số tháng từ chuỗi "Tháng 1" -> 1
            month_num = int(sel_month.replace("Tháng ", ""))
            df_filtered = df_filtered[df_filtered['THÁNG_SO_SANH'] == month_num]
            
        st.success(f"✅ Đã lọc: {len(df_filtered)} ca hỏng")
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN ---
st.markdown(f'<h1 style="text-align: center; color: #1E3A8A;">🛡️ BÁO CÁO CHI TIẾT {sel_month.upper()} / {sel_year}</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # CHỈ SỐ
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_filtered):,}")
    c2.metric("Số thiết bị lỗi", f"{df_filtered['MÃ_MÁY'].nunique():,}")
    
    heavy = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng >2 lần", len(heavy[heavy > 2]))
    c4.metric("Đơn vị yêu cầu", df_filtered['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3 = st.tabs(["📊 BIỂU ĐỒ & THỐNG KÊ", "🔍 TRUY LỤC", "🚩 DANH SÁCH ĐEN"])

    with tab1:
        st.subheader(f"🛠️ Top linh kiện lỗi trong {sel_month}")
        top_err = df_filtered[df_filtered['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
        st.bar_chart(top_err)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📍 Tỷ lệ Vùng Miền")
            fig = px.pie(df_filtered['VÙNG_MIỀN'].value_counts().reset_index(), values='count', names='VÙNG_MIỀN', hole=0.5)
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.subheader("📋 Chi tiết số lượng lỗi")
            st.dataframe(df_filtered['LINH_KIỆN_HƯ'].value_counts().reset_index().rename(columns={'count':'Số lượng'}), use_container_width=True)

    with tab2:
        q = st.text_input(f"Tìm mã máy trong {sel_month}:")
        if q:
            res = df_filtered[df_filtered['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['NGÀY_DT', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN_HƯ']], use_container_width=True)

    with tab3:
        st.subheader(f"🚩 Máy hỏng nhiều lần (Chỉ tính trong {sel_month})")
        list_h = heavy[heavy > 2].reset_index()
        list_h.columns = ['MÃ_MÁY', 'SỐ_LẦN_HỎNG']
        st.dataframe(list_h, use_container_width=True)

else:
    st.warning(f"⚠️ Không có dữ liệu hư hỏng nào được ghi nhận trong {sel_month} năm {sel_year}.")
