import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 - V58", layout="wide")

# LINK CSV (Sếp giữ nguyên link này)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v58():
    try:
        # Ép Google trả về dữ liệu mới nhất
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc toàn bộ file dưới dạng văn bản để không bị lỗi định dạng
        df = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        if df.empty: return None

        # CHẾ ĐỘ QUÉT SIÊU VIỆT: Tìm cột theo từ khóa nội dung
        def find_col_by_keywords(df, keywords):
            for col in df.columns:
                # Kiểm tra nội dung 50 dòng đầu của cột
                content_sample = " ".join(df[col].astype(str).head(50)).upper()
                if any(k in content_sample for k in keywords):
                    return col
            return None

        # Tìm cột dựa trên dữ liệu thực tế sếp nhập
        col_ma = find_col_by_keywords(df, ['3534', '1102', 'LAPTOP', 'MÃ']) or df.columns[1]
        col_ly = find_col_by_keywords(df, ['LỖI', 'THAY', 'HỎNG', 'SỬA', 'YẾU']) or df.columns[3]
        col_ng = find_col_by_keywords(df, ['2023', '2024', '2025', '2026']) or df.columns[0]

        # Tạo bảng dữ liệu chuẩn
        clean_df = pd.DataFrame()
        clean_df['MÃ_MÁY'] = df[col_ma].astype(str).str.split('.').str[0].str.strip()
        clean_df['LÝ_DO'] = df[col_ly].astype(str).str.strip()
        clean_df['NGÀY_GỐC'] = pd.to_datetime(df[col_ng], dayfirst=True, errors='coerce')
        
        # LỌC BỎ DỮ LIỆU NHIỄU (Tên hãng máy đang làm hỏng biểu đồ)
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE', 'MACBOOK', 'TOSHIBA']
        clean_df = clean_df[~clean_df['LÝ_DO'].str.upper().isin(hang_may)]
        
        # Chỉ lấy những dòng có mã máy thực sự (độ dài > 2)
        clean_df = clean_df[clean_df['MÃ_MÁY'].str.len() > 2].copy()
        
        # Thêm cột thời gian
        clean_df['NĂM'] = clean_df['NGÀY_GỐC'].dt.year.fillna(2026).astype(int)
        clean_df['THÁNG'] = clean_df['NGÀY_GỐC'].dt.month.fillna(1).astype(int)
        
        return clean_df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ BỘ LỌC HỆ THỐNG")
    if st.button('🔄 LÀM MỚI 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v58()
    if data is not None:
        st.success(f"✅ Đã kết nối {len(data)} dòng")
        
        # Lọc Năm & Tháng
        y_list = sorted([y for y in data['NĂM'].unique() if y > 2020], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + y_list)
        sel_month = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])
        
        df_display = data.copy()
        if sel_year != "Tất cả": df_display = df_display[df_display['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_display = df_display[df_display['THÁNG'] == m_num]
    else:
        df_display = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ QUẢN TRỊ LIVE DATA 3.651</h1>', unsafe_allow_html=True)

if not df_display.empty:
    # HIỂN THỊ CHỈ SỐ
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca hỏng", len(df_display))
    c2.metric("Số thiết bị", df_display['MÃ_MÁY'].nunique())
    
    # Tính máy hỏng nặng (> 3 lần)
    heavy_fix = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng nặng (>3 lần)", len(heavy_fix[heavy_fix > 3]))

    tab1, tab2 = st.tabs(["📊 BIỂU ĐỒ LỖI LINH KIỆN", "🔍 TRA CỨU MÃ MÁY"])
    
    with tab1:
        st.subheader("🛠️ Top 10 linh kiện lỗi nhiều nhất")
        # Chỉ lấy các lý do có nội dung thật sự
        chart_data = df_display[df_display['LÝ_DO'].str.len() > 3]['LÝ_DO'].value_counts().head(10)
        if not chart_data.empty:
            st.bar_chart(chart_data)
        else:
            st.info("Chưa có dữ liệu lỗi để vẽ biểu đồ.")

    with tab2:
        q = st.text_input("Nhập mã máy (Ví dụ: 3534):")
        if q:
            # Tìm trên toàn bộ dữ liệu gốc
            search_res = data[data['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(search_res[['NGÀY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)
else:
    st.info("💡 Đang nạp dữ liệu từ Google Sheets. Sếp hãy đợi vài giây...")
