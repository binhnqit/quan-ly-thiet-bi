import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="AI QUẢN TRỊ 3651 DÒNG - V45", layout="wide")

# 2. THAY LINK CSV MỚI CỦA SẾP VÀO ĐÂY
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v45():
    try:
        # Phá cache để lấy đúng 3.651 dòng
        df = pd.read_csv(f"{DATA_URL}&cache={time.time()}", on_bad_lines='skip', dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns] # Viết hoa hết tên cột để dễ tìm
        
        # Tự động tìm cột thông minh
        col_ma = [c for c in df.columns if 'MÃ' in c][0]
        col_lydo = [c for c in df.columns if 'LÝ DO' in c or 'NỘI DUNG' in c][0]
        col_ngay = [c for c in df.columns if 'NGÀY' in c][0]
        
        new_df = pd.DataFrame()
        new_df['NGÀY'] = pd.to_datetime(df[col_ngay], dayfirst=True, errors='coerce')
        new_df['MÃ_MÁY'] = df[col_ma].str.split('.').str[0].str.strip()
        new_df['NỘI_DUNG'] = df[col_lydo].fillna("Trống")
        
        # Tạo cột tìm kiếm tổng hợp
        new_df['SEARCH_KEY'] = new_df['MÃ_MÁY'].astype(str) + " " + new_df['NỘI_DUNG'].astype(str)
        return new_df
    except Exception as e:
        return None

# --- GIAO DIỆN ---
with st.sidebar:
    st.header("⚙️ HỆ THỐNG")
    if st.button('🚀 CẬP NHẬT 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()

df_raw = load_data_v45()

if df_raw is not None:
    st.success(f"📊 Đã kết nối thành công: {len(df_raw)} dòng dữ liệu")
    
    # BỘ LỌC THỜI GIAN
    years = sorted(df_raw['NGÀY'].dt.year.dropna().unique().astype(int), reverse=True)
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("📅 Chọn Năm", ["Tất cả"] + years)
    
    # CHỨC NĂNG TÌM KIẾM CHÍNH (Tab Tìm Kiếm)
    st.divider()
    st.subheader("🔍 TRUY LỤC LỊCH SỬ THIẾT BỊ")
    q = st.text_input("Nhập Mã máy hoặc Tên linh kiện (Ví dụ: 3534 hoặc Màn hình):")
    
    if q:
        # Tìm trong toàn bộ 3651 dòng, không bị giới hạn bởi bộ lọc năm
        res = df_raw[df_raw['SEARCH_KEY'].str.contains(q, case=False, na=False)]
        st.info(f"Tìm thấy {len(res)} kết quả cho từ khóa '{q}'")
        st.dataframe(res[['NGAY', 'MÃ_MÁY', 'NỘI_DUNG']].sort_values('NGAY', ascending=False), use_container_width=True)
    else:
        st.write("💡 *Mẹo: Nhập mã máy để xem tất cả lần hỏng trong quá khứ.*")

else:
    st.error("❌ Lỗi link hoặc định dạng Sheets. Sếp hãy kiểm tra lại Bước 1 nhé!")
