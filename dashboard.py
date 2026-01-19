import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống AI 3651 - V51", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v51():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu thô
        df_raw = pd.read_csv(url, header=None, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- CHIẾN THUẬT QUÉT DÒNG TIÊU ĐỀ ---
        header_idx = 0
        found = False
        for i in range(min(15, len(df_raw))):
            line_str = " ".join([str(x) for x in df_raw.iloc[i]]).upper()
            if 'MÃ' in line_str or 'NGÀY' in line_str or 'LÝ DO' in line_str:
                header_idx = i
                found = True
                break
        
        if not found:
            return None

        # Thiết lập DataFrame
        headers = [str(c).strip().upper() for c in df_raw.iloc[header_idx]]
        df = df_raw.iloc[header_idx+1:].copy()
        df.columns = headers
        
        # Tìm cột cần thiết
        def find_col(keywords):
            for k in keywords:
                for name in headers:
                    if k in name: return name
            return None

        c_ma = find_col(['MÃ', 'MA', 'ID'])
        c_ly = find_col(['LÝ DO', 'NỘI DUNG', 'CHI TIẾT', 'LOI'])
        c_ng = find_col(['NGÀY', 'NGAY', 'DATE'])

        if not c_ma or not c_ng:
            return None

        # Chuyển đổi dữ liệu sạch
        new_df = pd.DataFrame()
        new_df['MÃ_MÁY'] = df[c_ma].astype(str).str.split('.').str[0].str.strip()
        new_df['LÝ_DO'] = df[c_ly].astype(str).str.strip()
        new_df['NGÀY_GỐC'] = pd.to_datetime(df[c_ng], dayfirst=True, errors='coerce')
        
        # Lọc bỏ dòng trống
        new_df = new_df[new_df['MÃ_MÁY'] != ""]
        
        # Tạo Năm/Tháng
        new_df['NĂM'] = new_df['NGÀY_GỐC'].dt.year.fillna(0).astype(int)
        new_df['THÁNG_SO'] = new_df['NGAY_GỐC'].dt.month.fillna(0).astype(int)
        
        return new_df
    except Exception:
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🚀 KẾT NỐI 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v51()
    if data is not None:
        st.success(f"✅ Đã nhận {len(data)} dòng")
        years = sorted([y for y in data['NĂM'].unique() if y > 0], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + years)
        
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", months)
        
        df_final = data.copy()
        if sel_year != "Tất cả":
            df_final = df_final[df_final['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_final = df_final[df_final['THÁNG_SO'] == m_num]
    else:
        st.error("Chưa tìm thấy dữ liệu chuẩn.")
        df_final = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if not df_final.empty:
    tab1, tab2 = st.tabs(["🔍 TÌM KIẾM LỊCH SỬ", "📊 BÁO CÁO THỐNG KÊ"])
    
    with tab1:
        st.subheader("🔎 Nhập Mã máy để kiểm tra")
        q = st.text_input("Gõ mã thiết bị (Ví dụ: 3534):")
        if q:
            # Tìm trong 3651 dòng
            res = data[data['MÃ_MÁY'].str.contains(q, na=False, case=False)]
            st.info(f"Tìm thấy {len(res)} lượt sửa chữa.")
            st.dataframe(res[['NGÀY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)
    
    with tab2:
        st.metric("Tổng số ca ghi nhận", len(df_final))
        if not df_final['LÝ_DO'].empty:
            st.subheader("Top 10 lỗi nhiều nhất")
            st.bar_chart(df_final['LÝ_DO'].value_counts().head(10))
else:
    st.info("💡 Hệ thống đang chờ kết nối dữ liệu từ Google Sheets.")import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 - V50", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v50():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc toàn bộ file thô dưới dạng String để tránh lỗi định dạng
        df_raw = pd.read_csv(url, header=None, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- CHIẾN THUẬT QUÉT DÒNG TIÊU ĐỀ AN TOÀN ---
        header_idx = 0
        found = False
        
        # Quét 10 dòng đầu tiên để tìm dòng chứa tiêu đề thực sự
        for i in range(min(10, len(df_raw))):
            # Chuyển toàn bộ dòng thành chuỗi để tìm kiếm
            line_str = " ".join([str(x) for x in df_raw.iloc[i]]).upper()
            if 'MÃ' in line_str or 'NGÀY' in line_str or 'ID' in line_str:
                header_idx = i
                found = True
                break
        
        if not found:
            st.error("❌ AI không tìm thấy dòng tiêu đề có chữ 'Mã' hoặc 'Ngày'. Sếp hãy kiểm tra lại dòng 1-5 của file Sheets.")
            return None

        # Thiết lập lại DataFrame từ dòng tìm được
        headers = [str(c).strip().upper() for c in df_raw.iloc[header_idx]]
        df = df_raw.iloc[header_idx+1:].copy()
        df.columns = headers
        
        # Tìm cột thông minh bằng cách quét tên
        def find_col(keywords):
            for k in keywords:
                for idx, name in enumerate(headers):
                    if k in name: return name
            return None

        c_ma = find_col(['MÃ', 'MA', 'ID'])
        c_ly = find_col(['LÝ DO', 'NỘI DUNG', 'CHI TIẾT', 'LOI'])
        c_ng = find_col(['NGÀY', 'NGAY', 'DATE'])

        if not c_ma or not c_ng:
            st.warning(f
