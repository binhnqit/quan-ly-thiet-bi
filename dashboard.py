import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 - V56", layout="wide")

# LINK CSV CHUẨN CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v56():
    try:
        # Phá cache Google
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu thô, ép kiểu chuỗi hoàn toàn để tránh lỗi 'upper'
        df = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        if df.empty: return None

        # CHIẾN THUẬT: TỰ ĐỘNG CHUẨN HÓA CỘT
        # Chúng ta sẽ làm sạch tên cột để AI dễ nhận diện hơn
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Tìm cột thông minh không phụ thuộc vị trí
        def find_best_col(targets):
            for t in targets:
                for col in df.columns:
                    if t in col: return col
            return None

        c_ma = find_best_col(['MÃ', 'MA', 'ID', 'DEVICE'])
        c_ly = find_best_col(['LÝ DO', 'NỘI DUNG', 'CHI TIẾT', 'LOI'])
        c_ng = find_best_col(['NGÀY', 'NGAY', 'DATE'])

        # Nếu không tìm thấy tên cột, lấy đại diện theo vị trí phổ biến nhất
        if not c_ma: c_ma = df.columns[1]
        if not c_ly: c_ly = df.columns[3]
        if not c_ng: c_ng = df.columns[6]

        # Xử lý dữ liệu
        res_df = pd.DataFrame()
        res_df['MÃ_MÁY'] = df[c_ma].astype(str).str.split('.').str[0].str.strip()
        res_df['LÝ_DO'] = df[c_ly].astype(str).str.strip()
        res_df['NGÀY_GỐC'] = pd.to_datetime(df[c_ng], dayfirst=True, errors='coerce')
        
        # Lọc dòng trống
        res_df = res_df[res_df['MÃ_MÁY'] != ""].copy()
        
        # Tạo cột Năm/Tháng cho biểu đồ
        res_df['NĂM'] = res_df['NGÀY_GỐC'].dt.year.fillna(2026).astype(int)
        res_df['THÁNG'] = res_df['NGÀY_GỐC'].dt.month.fillna(1).astype(int)
        
        return res_df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🚀 CẬP NHẬT DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v56()
    if data is not None:
        st.success(f"✅ Đã kết nối {len(data)} dòng")
        
        years = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Năm báo cáo", ["Tất cả"] + list(years))
        
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Tháng báo cáo", months)
        
        df_final = data.copy()
        if sel_year != "Tất cả": df_final = df_final[df_final['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_final = df_final[df_final['THÁNG'] == m_num]
    else:
        df_final = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_final.empty:
    # 3 CHỈ SỐ CHÍNH
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Tổng ca hỏng", len(df_final))
    with c2: st.metric("Số thiết bị", df_final['MÃ_MÁY'].nunique())
    with c3:
        hard_fix = df_final['MÃ_MÁY'].value_counts()
        st.metric("Máy hỏng nặng (>3 lần)", len(hard_fix[hard_fix > 3]))

    tab1, tab2 = st.tabs(["📊 BIỂU ĐỒ & THỐNG KÊ", "🔍 TRUY LỤC CHI TIẾT"])
    
    with tab1:
        st.subheader("📈 Thống kê linh kiện lỗi")
        # Fix lỗi biểu đồ biến mất: Luôn đảm bảo có dữ liệu trước khi vẽ
        top_errors = df_final['LÝ_DO'].value_counts().head(10)
        if not top_errors.empty:
            st.bar_chart(top_errors)
        else:
            st.info("Không có dữ liệu biểu đồ cho thời gian này.")

    with tab2:
        search = st.text_input("Gõ mã máy để xem lịch sử (Ví dụ: 3534):")
        if search:
            # Tìm trên toàn bộ data để sếp không bị mất lịch sử cũ
            search_res = data[data['MÃ_MÁY'].str.contains(search, na=False, case=False)]
            st.dataframe(search_res[['NGÀY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)
else:
    st.warning("⚠️ Đang xử lý dữ liệu... Nếu thấy hiện số 0, sếp hãy nhấn nút 'Cập nhật dữ liệu' ở Sidebar.")
