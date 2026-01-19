import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN
st.set_page_config(page_title="Hệ Thống AI 3651 - V55", layout="wide")

# LINK CSV CHUẨN (ĐÃ XÁC THỰC)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_and_clean_data():
    try:
        # Phá cache Google Sheets để lấy đúng 3.651 dòng
        url = f"{DATA_URL}&cache={time.time()}"
        
        # Bước 1: Đọc thô không lấy tiêu đề để dò tìm dòng chứa dữ liệu thật
        df_raw = pd.read_csv(url, header=None, on_bad_lines='skip', dtype=str).fillna("")
        
        # Bước 2: Dò tìm dòng tiêu đề thực sự (Tìm dòng có chữ 'MÃ' hoặc 'NGÀY')
        target_row = 0
        for i in range(min(15, len(df_raw))):
            row_str = " ".join(df_raw.iloc[i].values).upper()
            if 'MÃ' in row_str or 'NGÀY' in row_str:
                target_row = i
                break
        
        # Bước 3: Thiết lập lại DataFrame từ dòng tiêu đề tìm được
        headers = [str(h).strip().upper() for h in df_raw.iloc[target_row]]
        df = df_raw.iloc[target_row + 1:].copy()
        df.columns = headers

        # Bước 4: Định danh cột thông minh (Dù sếp chèn thêm cột vẫn không lệch)
        def get_col_name(keys, default_idx):
            for k in keys:
                for col in headers:
                    if k in col: return col
            return headers[default_idx] if default_idx < len(headers) else headers[0]

        c_ma = get_col_name(['MÃ', 'MA', 'ID'], 1)
        c_ly = get_col_name(['LÝ DO', 'NỘI DUNG', 'CHI TIẾT'], 3)
        c_ng = get_col_name(['NGÀY', 'NGAY', 'DATE'], 6)

        # Bước 5: Chuyển đổi và làm sạch dữ liệu
        final_df = pd.DataFrame()
        final_df['MÃ_MÁY'] = df[c_ma].astype(str).str.split('.').str[0].str.strip()
        final_df['LÝ_DO'] = df[c_ly].astype(str).str.strip()
        final_df['NGÀY_GỐC'] = pd.to_datetime(df[c_ng], dayfirst=True, errors='coerce')
        
        # Bỏ các dòng rác (không có mã máy)
        final_df = final_df[final_df['MÃ_MÁY'] != ""].copy()
        
        # Tạo cột thời gian phục vụ bộ lọc Sidebar
        final_df['NĂM'] = final_df['NGÀY_GỐC'].dt.year.fillna(0).astype(int)
        final_df['THÁNG'] = final_df['NGÀY_GỐC'].dt.month.fillna(0).astype(int)
        
        return final_df
    except Exception as e:
        st.error(f"❌ Lỗi xử lý dữ liệu: {e}")
        return None

# --- SIDEBAR: ĐIỀU KHIỂN ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ HỆ THỐNG")
    if st.button('🚀 ĐỒNG BỘ DỮ LIỆU MỚI'):
        st.cache_data.clear()
        st.rerun()
    
    all_data = load_and_clean_data()
    
    if all_data is not None:
        st.success(f"✅ Đã kết nối {len(all_data)} dòng")
        
        # Bộ lọc Năm (Tự động lấy các năm có trong dữ liệu)
        years = sorted([y for y in all_data['NĂM'].unique() if y > 0], reverse=True)
        sel_year = st.selectbox("📅 Xem theo Năm", ["Tất cả"] + years)
        
        # Bộ lọc Tháng
        sel_month = st.selectbox("📆 Xem theo Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])
        
        # Xử lý lọc dữ liệu cho Dashboard
        df_view = all_data.copy()
        if sel_year != "Tất cả":
            df_view = df_view[df_view['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_idx = int(sel_month.split(" ")[1])
            df_view = df_view[df_view['THÁNG'] == m_idx]
    else:
        df_view = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)
st.divider()

if all_data is not None and not all_data.empty:
    tab1, tab2, tab3 = st.tabs(["🔍 TÌM KIẾM LỊCH SỬ", "📊 BÁO CÁO THÁNG", "🚩 CẢNH BÁO"])
    
    with tab1:
        st.subheader("🔎 Tra cứu thiết bị trong toàn bộ 3.651 dòng")
        q = st.text_input("Nhập Mã thiết bị (VD: 3534) hoặc tên linh kiện:", key="search")
        if q:
            # Tìm trên TOÀN BỘ dữ liệu, không bị giới hạn bởi bộ lọc Sidebar
            res = all_data[
                all_data['MÃ_MÁY'].str.contains(q, case=False, na=False) | 
                all_data['LÝ_DO'].str.contains(q, case=False, na=False)
            ]
            st.info(f"Tìm thấy {len(res)} kết quả liên quan.")
            st.dataframe(res[['NGÀY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)
        else:
            st.write("💡 *Nhập mã máy để thấy lịch sử sửa chữa từ trước đến nay.*")

    with tab2:
        st.write(f"📂 Đang hiển thị thống kê: **{sel_month} / {sel_year}**")
        c1, c2 = st.columns(2)
        c1.metric("Tổng lượt sửa", len(df_view))
        c2.metric("Số máy hư hỏng", df_view['MÃ_MÁY'].nunique())
        
        if not df_view.empty:
            st.bar_chart(df_view['LÝ_DO'].value_counts().head(10))
        else:
            st.warning("Không có dữ liệu trong khoảng thời gian này.")

    with tab3:
        st.subheader("🚩 Máy hỏng nhiều (Trên 3 lần)")
        bad_devices = all_data['MÃ_MÁY'].value_counts()
        bad_devices = bad_devices[bad_devices >= 3].reset_index()
        bad_devices.columns = ['Mã Máy', 'Số Lần Hỏng']
        st.table(bad_devices)

else:
    st.warning("⚠️ Đang chờ dữ liệu... Sếp hãy kiểm tra link Google Sheets hoặc nhấn 'Đồng bộ' ở Sidebar.")
