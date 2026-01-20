import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH ---
st.set_page_config(page_title="Quản Lý Thiết Bị V8000", layout="wide")

@st.cache_data(ttl=2)
def load_data_final():
    # URL CSV từ Google Sheets
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    try:
        # Đọc dữ liệu thô, bỏ qua 3 dòng đầu nếu đó là phần tiêu đề trang trí
        df_raw = pd.read_csv(url, dtype=str, header=None, skiprows=1).fillna("")
        
        clean_data = []
        for i, row in df_raw.iterrows():
            # ÁNH XẠ ĐÚNG CỘT THEO ẢNH SẾP GỬI:
            # Cột B (index 1): Mã số máy
            # Cột C (index 2): Tên KH
            # Cột D (index 3): Lý do
            # Cột F (index 5): Chi nhánh
            # Cột G (index 6): Ngày xác nhận
            
            ma_may = str(row.iloc[1]).strip()
            ten_kh = str(row.iloc[2]).strip()
            ly_do = str(row.iloc[3]).strip()
            chi_nhanh = str(row.iloc[5]).strip()
            ngay_raw = str(row.iloc[6]).strip()

            # MASTER KEY: Chỉ lấy dòng có Mã số máy
            if not ma_may or len(ma_may) < 2 or "MÃ" in ma_may.upper():
                continue

            # Chuyển đổi ngày tháng
            p_date = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            
            if pd.notnull(p_date):
                clean_data.append({
                    "NGÀY": p_date,
                    "NĂM": p_date.year,
                    "THÁNG": p_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": ten_kh if ten_kh else "N/A",
                    "LINH_KIỆN": ly_do if ly_do else "Chưa xác định",
                    "VÙNG": chi_nhanh if chi_nhanh else "Không xác định"
                })
        
        return pd.DataFrame(clean_data)
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu: {e}")
        return pd.DataFrame()

# --- KHỞI CHẠY ---
df = load_data_final()

st.title("🛡️ HỆ THỐNG GIÁM SÁT THIẾT BỊ V8000")

if not df.empty:
    # Sidebar lọc
    with st.sidebar:
        st.header("⚙️ BỘ LỌC")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU'):
            st.cache_data.clear()
            st.rerun()
        
        list_year = sorted(df['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_year)
        
    df_final = df[df['NĂM'] == sel_year]

    # KPI 
    c1, c2, c3, c4
