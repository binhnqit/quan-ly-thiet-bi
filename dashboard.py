import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V47", layout="wide")

# 2. LINK CSV CHUẨN SẾP VỪA GỬI
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v47():
    try:
        # Phá cache để đảm bảo lấy đủ 3.651 dòng
        final_url = f"{DATA_URL}&cache_buster={time.time()}"
        df = pd.read_csv(final_url, on_bad_lines='skip', dtype=str)
        
        # Làm sạch tên cột (Viết hoa, bỏ khoảng trắng)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # --- CHIẾN THUẬT TÌM CỘT THÔNG MINH ---
        # AI tự dò cột dù sếp có chèn thêm hay đổi vị trí cột
        col_ma = [c for c in df.columns if 'MÃ' in c or 'ID' in c][0]
        col_lydo = [c for c in df.columns if 'LÝ DO' in c or 'NỘI DUNG' in c or 'HƯ HỎNG' in c][0]
        col_ngay = [c for c in df.columns if 'NGÀY' in c][0]
        
        # Tạo bảng dữ liệu chuẩn để xử lý
        new_df = pd.DataFrame()
        new_df['MÃ_MÁY'] = df[col_ma].str.split('.').str[0].str.strip()
        new_df['NỘI_DUNG'] = df[col_lydo].fillna("Trống")
        new_df['NGÀY_FIX'] = pd.to_datetime(df[col_ngay], dayfirst=True, errors='coerce')
        
        # Tách Năm và Tháng để làm bộ lọc
        new_df['NĂM'] = new_df['NGÀY_FIX'].dt.year.fillna(0).astype(int)
        new_df['THÁNG_SO'] = new_df['NGAY_FIX'].dt.month.fillna(0).astype(int)
        
        # Cột tìm kiếm tổng hợp (Gộp Mã máy và Nội dung để tìm kiếm chuẩn 100%)
        new_df['SEARCH_ALL'] = new_df['MÃ_MÁY'].astype(str) + " " + new_df['NỘI_DUNG'].astype(str)
        
        return new_df
    except Exception as e:
        st.error(f"⚠️ Lỗi cấu trúc Sheets: AI không tìm thấy cột 'Mã' hoặc 'Ngày'. Sếp hãy kiểm tra tiêu đề dòng 1 nhé!")
        return None

# --- SIDEBAR: BỘ LỌC THỜI GIAN ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ DỮ LIỆU")
    if st.button('🔄 CẬP NHẬT 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()

    df_all = load_data_v47()
    
    if df_all is not None:
        st.success(f"✅ Đã nhận {len(df_all)} dòng") # Phải hiện 3651 ở đây mới đúng
        
        # Lọc Năm
        years = ["Tất cả"] + sorted([int(y) for y in df_all['NĂM'].unique() if y != 0], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", years)
        
        # Lọc Tháng
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", months)
        
        # Áp dụng lọc cho Dashboard
        df_view = df_all.copy()
        if sel_year != "Tally":
            df_view = df_view[df_view['NĂM'] == sel_year]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_view = df_view[df_view['THÁNG_SO'] == m_num]
    else:
        df_view = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ AI TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if not df_view.empty:
    tab1, tab2 = st.tabs(["🔍 TÌM KIẾM CHÍNH XÁC", "📊 BÁO CÁO THÁNG"])
    
    with tab1:
        st.subheader("🔎 Nhập Mã máy hoặc Tên linh kiện")
        keyword = st.text_input("Ví dụ: '3534' hoặc 'Màn hình'", placeholder="AI sẽ lục lại toàn bộ lịch sử 3.651 dòng...")
        
        if keyword:
            # TÌM KIẾM TOÀN CỤC: Lục trong df_all (toàn bộ data) chứ không chỉ trong tháng đang lọc
            results = df_all[df_all['SEARCH_ALL'].str.contains(keyword, case=False, na=False)]
            st.info(f"Tìm thấy {len(results)} kết quả trong toàn bộ lịch sử.")
            st.dataframe(results[['NGÀY_FIX', 'MÃ_MÁY', 'NỘI_DUNG']].sort_values('NGÀY_FIX', ascending=False), use_container_width=True)

    with tab2:
        st.write(f"📂 Thống kê cho: **{sel_month} / {sel_year}**")
        col1, col2 = st.columns(2)
        col1.metric("Tổng lượt sửa", len(df_view))
        col2.metric("Số máy hư hỏng", df_view['MÃ_MÁY'].nunique())
        
        # Biểu đồ linh kiện hỏng nhiều nhất tháng
        st.bar_chart(df_view['NỘI_DUNG'].value_counts().head(10))
else:
    st.warning("⚠️ Không có dữ liệu hoặc đang tải. Sếp nhấn 'CẬP NHẬT' nhé!")
