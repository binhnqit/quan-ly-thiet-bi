import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="AI QUẢN TRỊ 3651 DÒNG - V46", layout="wide")

# 2. DÁN LINK CSV CHUẨN (CÓ CHỮ =csv Ở CUỐI) VÀO ĐÂY
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v46():
    try:
        # Ép hệ thống tải mới hoàn toàn 3651 dòng
        df = pd.read_csv(f"{DATA_URL}&cache={time.time()}", on_bad_lines='skip', dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Tự động nhận diện cột thông minh (Không lo lệch cột)
        col_ma = [c for c in df.columns if 'MÃ' in c][0]
        col_lydo = [c for c in df.columns if 'LÝ DO' in c or 'NỘI DUNG' in c][0]
        col_ngay = [c for c in df.columns if 'NGÀY' in c][0]
        
        df_clean = pd.DataFrame()
        df_clean['NGÀY_GỐC'] = pd.to_datetime(df[col_ngay], dayfirst=True, errors='coerce')
        df_clean['MÃ_MÁY'] = df[col_ma].str.split('.').str[0].str.strip()
        df_clean['LÝ_DO'] = df[col_lydo].fillna("Trống")
        df_clean['NĂM'] = df_clean['NGAY_GỐC'].dt.year.fillna(2026).astype(int)
        df_clean['THÁNG_SO'] = df_clean['NGAY_GỐC'].dt.month.fillna(1).astype(int)
        
        # Ghép từ khóa tìm kiếm
        df_clean['SEARCH_KEY'] = df_clean['MÃ_MÁY'].astype(str) + " " + df_clean['LÝ_DO'].astype(str)
        return df_clean
    except Exception as e:
        return None

# --- SIDEBAR: BỘ LỌC CHÍNH ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN")
    if st.button('🚀 ĐỒNG BỘ 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    df_raw = load_data_v46()
    
    if df_raw is not None:
        st.success(f"✅ Đã nhận: {len(df_raw)} dòng")
        
        # Chọn Năm
        years = sorted(df_raw['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + [int(y) for y in years])
        
        # Chọn Tháng
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", months)
        
        # Lọc dữ liệu theo Sidebar
        df_filtered = df_raw if sel_year == "Tất cả" else df_raw[df_raw['NĂM'] == sel_year]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_filtered = df_filtered[df_filtered['THÁNG_SO'] == m_num]

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if df_raw is not None:
    tab1, tab2 = st.tabs(["🔍 TÌM KIẾM CHÍNH XÁC", "📊 THỐNG KÊ CHI TIẾT"])
    
    with tab1:
        st.subheader("🔎 Nhập Mã máy để xem lịch sử")
        q = st.text_input("Gõ mã (VD: 3534) hoặc lỗi (VD: Màn hình):", placeholder="Lục lại lịch sử trong 3.651 dòng...")
        
        if q:
            # Tìm trên toàn bộ 3651 dòng (không bị giới hạn bởi bộ lọc tháng/năm)
            res = df_raw[df_raw['SEARCH_KEY'].str.contains(q, case=False, na=False)]
            st.info(f"Tìm thấy {len(res)} lượt sửa chữa trong lịch sử.")
            st.dataframe(res[['NGAY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)

    with tab2:
        st.write(f"📂 Đang thống kê: {sel_month} / {sel_year}")
        c1, c2 = st.columns(2)
        c1.metric("Số ca sửa", len(df_filtered))
        c2.metric("Số máy lỗi", df_filtered['MÃ_MÁY'].nunique())
        
        if not df_filtered.empty:
            st.bar_chart(df_filtered['LÝ_DO'].value_counts().head(10))
else:
    st.error("⚠️ Vui lòng kiểm tra lại Bước 1: Xuất bản link dạng CSV.")
