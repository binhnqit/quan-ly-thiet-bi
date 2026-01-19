import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN
st.set_page_config(page_title="Hệ Thống AI 3651 - V60", layout="wide")

# SẾP DÁN CÁI LINK CỦA RIÊNG TAB 3.651 DÒNG VÀO ĐÂY NHÉ
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=1)
def load_data_v60():
    try:
        # Phá cache để lấy dữ liệu thời thực
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu, bỏ qua các dòng lỗi, ép kiểu chuỗi
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        if df_raw.empty: return None

        # --- CHIẾN THUẬT TỰ CÂN CHỈNH CỘT (DÙNG NỘI DUNG ĐỂ ĐOÁN) ---
        new_df = pd.DataFrame()
        
        # 1. Tìm cột MÃ MÁY: Cột nào chứa các mã như 3534, 1102...
        col_ma = None
        for col in df_raw.columns:
            if df_raw[col].astype(str).str.contains(r'\d{4}', na=False).any():
                col_ma = col
                break
        
        # 2. Tìm cột LÝ DO: Cột nào có chữ "Thay", "Lỗi", "Hỏng"
        col_ly = None
        keywords = ['THAY', 'LỖI', 'HỎNG', 'SỬA', 'CÀI', 'LIỆT', 'VỠ']
        for col in df_raw.columns:
            sample = " ".join(df_raw[col].astype(str).head(100)).upper()
            if any(k in sample for k in keywords):
                col_ly = col
                break

        # 3. Tìm cột NGÀY: Cột có định dạng ngày tháng
        col_ng = None
        for col in df_raw.columns:
            if df_raw[col].astype(str).str.contains(r'\d{1,2}/\d{1,2}', na=False).any():
                col_ng = col
                break

        # Gán mặc định nếu không quét được
        col_ma = col_ma if col_ma else df_raw.columns[1]
        col_ly = col_ly if col_ly else df_raw.columns[3]
        col_ng = col_ng if col_ng else df_raw.columns[0]

        # Xây dựng DataFrame chuẩn để vẽ biểu đồ và tìm kiếm
        new_df['MÃ_MÁY'] = df_raw[col_ma].astype(str).str.split('.').str[0].str.strip()
        new_df['LÝ_DO'] = df_raw[col_ly].astype(str).str.strip()
        new_df['NGÀY_GỐC'] = pd.to_datetime(df_raw[col_ng], dayfirst=True, errors='coerce')
        
        # Lọc bỏ dòng rác (Mã máy phải có độ dài nhất định)
        new_df = new_df[new_df['MÃ_MÁY'].str.len() >= 3].copy()
        
        # Loại bỏ các dòng bị nhầm sang Tên Hãng để biểu đồ chuẩn hơn
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE']
        new_df = new_df[~new_df['LÝ_DO'].str.upper().isin(hang_may)]

        new_df['NĂM'] = new_df['NGÀY_GỐC'].dt.year.fillna(2026).astype(int)
        new_df['THÁNG'] = new_df['NGÀY_GỐC'].dt.month.fillna(1).astype(int)
        
        return new_df
    except Exception as e:
        st.error(f"Lỗi rà soát: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN V60")
    if st.button('🚀 ÉP ĐỒNG BỘ 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v60()
    if data is not None:
        st.success(f"✅ Đã kết nối {len(data)} dòng")
        
        y_list = sorted([y for y in data['NĂM'].unique() if y > 2020], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + y_list)
        sel_month = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])
        
        df_view = data.copy()
        if sel_year != "Tất cả": df_view = df_view[df_view['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_view = df_view[df_view['THÁNG'] == m_num]
    else:
        df_view = pd.DataFrame()

# --- GIAO DIỆN ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ QUẢN TRỊ TÀI SẢN CHI TIẾT 2026</h1>', unsafe_allow_html=True)

if not df_view.empty:
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca hỏng", len(df_view))
    c2.metric("Số thiết bị", df_view['MÃ_MÁY'].nunique())
    
    heavy = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng nặng (>3 lần)", len(heavy[heavy > 3]))

    t1, t2 = st.tabs(["📊 BIỂU ĐỒ LỖI", "🔍 TRUY LỤC MÃ MÁY"])
    
    with t1:
        st.subheader("📈 Thống kê linh kiện hỏng")
        # Chỉ vẽ biểu đồ nếu cột Lý do không rỗng
        top_err = df_view[df_view['LÝ_DO'].str.len() > 2]['LÝ_DO'].value_counts().head(10)
        if not top_err.empty:
            st.bar_chart(top_err)
        else:
            st.warning("Dữ liệu lý do hỏng đang bị trống hoặc sai cột.")

    with t2:
        q = st.text_input("Nhập mã máy (VD: 3534):", key="search_v60")
        if q:
            res = data[data['MÃ_MÁY'].str.contains(q, na=False)]
            # Kiểm tra cột trước khi sort để tránh lỗi KeyError
            if not res.empty and 'NGÀY_GỐC' in res.columns:
                st.dataframe(res[['NGÀY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGÀY_GỐC', ascending=False), use_container_width=True)
            else:
                st.dataframe(res)
else:
    st.warning("⚠️ Đang chờ dữ liệu... Sếp hãy kiểm tra Link CSV xem đã chọn đúng Tab 3.651 dòng chưa nhé.")
