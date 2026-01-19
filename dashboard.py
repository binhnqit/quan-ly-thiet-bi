import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V44", layout="wide")

# 2. DÁN LINK CSV MỚI CỦA SẾP VÀO ĐÂY (Link kết thúc bằng =csv)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1) # Ép tải mới liên tục
def load_data_v44():
    try:
        # Thêm mã phá cache cực mạnh
        final_url = f"{DATA_URL}&cache_buster={time.time()}"
        df = pd.read_csv(final_url, on_bad_lines='skip', dtype=str)
        
        # Làm sạch dữ liệu: Bỏ khoảng trắng trong tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        # TỰ ĐỘNG NHẬN DIỆN CỘT (Dù sếp có chèn thêm cột hay bớt cột)
        # Chúng ta tìm cột chứa chữ "Mã" và "Lý do" hoặc "Nội dung"
        col_ma = [c for c in df.columns if 'MÃ' in c.upper()][0]
        col_lydo = [c for c in df.columns if 'LÝ DO' in c.upper() or 'NỘI DUNG' in c.upper()][0]
        col_ngay = [c for c in df.columns if 'NGÀY' in c.upper()][0]
        
        # Tạo bảng dữ liệu chuẩn
        new_df = pd.DataFrame()
        new_df['MÃ_MÁY'] = df[col_ma].str.split('.').str[0].str.strip()
        new_df['LÝ_DO'] = df[col_lydo].fillna("Trống")
        new_df['NGAY_FIX'] = pd.to_datetime(df[col_ngay], dayfirst=True, errors='coerce')
        
        # Xử lý Năm/Tháng
        new_df['NĂM'] = new_df['NGAY_FIX'].dt.year.fillna(2026).astype(int)
        new_df['THÁNG_SO'] = new_df['NGAY_FIX'].dt.month.fillna(1).astype(int)
        
        # Gán vùng miền dựa trên nội dung dòng đó
        def get_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "SG", "HCM"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "HN", "MB"]): return "Miền Bắc"
            return "Khác/Văn Phòng"
            
        new_df['VÙNG'] = df.apply(get_region, axis=1)
        return new_df
    except Exception as e:
        st.error(f"Không tìm thấy cột chuẩn trong Sheets. Sếp kiểm tra tiêu đề cột nhé! ({e})")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN")
    if st.button('🚀 ÉP ĐỒNG BỘ 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()

df_raw = load_data_v44()

if df_raw is not None:
    with st.sidebar:
        st.success(f"✅ Đã kết nối: {len(df_raw)} dòng")
        
        years = ["Tất cả"] + sorted([int(y) for y in df_raw['NĂM'].unique()], reverse=True)
        sel_year = st.selectbox("📅 Năm", years)
        
        df_year = df_raw if sel_year == "Tất cả" else df_raw[df_raw['NĂM'] == sel_year]
        
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Tháng", months)
        
        if sel_month == "Tất cả":
            df_final = df_year
        else:
            m_num = int(sel_month.split(" ")[1])
            df_final = df_year[df_year['THÁNG_SO'] == m_num]

# --- GIAO DIỆN ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ QUẢN TRỊ TÀI SẢN CHI TIẾT 2026</h1>', unsafe_allow_html=True)

if df_raw is not None and not df_final.empty:
    t1, t2, t3 = st.tabs(["📊 Thống Kê", "🔍 Tìm Kiếm Chuẩn", "🚩 Cảnh Báo"])
    
    with t1:
        st.info(f"📁 Đang xem: {sel_month} / {sel_year} (Tổng {len(df_final)} ca)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_final)}")
        c2.metric("Thiết bị lỗi", f"{df_final['MÃ_MÁY'].nunique()}")
        c3.metric("Lượt hỏng nặng", f"{len(df_raw['MÃ_MÁY'].value_counts()[df_raw['MÃ_MÁY'].value_counts() >= 4])}")
        
        st.plotly_chart(px.bar(df_final['VÙNG'].value_counts().reset_index(), x='count', y='VÙNG', orientation='h', title="Sửa chữa theo khu vực"), use_container_width=True)

    with t2:
        st.subheader("🔍 Tìm kiếm chính xác (Theo Mã hoặc Nội dung)")
        search_q = st.text_input("Gõ mã máy (VD: 3534) hoặc tên linh kiện:", placeholder="AI sẽ lục trong toàn bộ 3.651 dòng...")
        
        if search_q:
            # Tìm kiếm trên TOÀN BỘ dữ liệu gốc để không bỏ sót lịch sử
            results = df_raw[
                df_raw['MÃ_MÁY'].astype(str).str.contains(search_q, case=False, na=False) | 
                df_raw['LÝ_DO'].astype(str).str.contains(search_q, case=False, na=False)
            ]
            st.success(f"Tìm thấy {len(results)} lượt sửa chữa.")
            st.dataframe(results[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with t3:
        st.subheader("🚩 Danh sách máy hỏng trên 4 lần")
        bad_list = df_raw['MÃ_MÁY'].value_counts()
        st.table(bad_list[bad_list >= 4])
else:
    st.warning("⚠️ Đang tải dữ liệu... Sếp hãy đảm bảo link CSV đã được xuất bản đúng cách.")
