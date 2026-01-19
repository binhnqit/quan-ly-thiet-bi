import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống AI 3651 - V57", layout="wide")

# LINK CSV TỔNG CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v57():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu thô, ép kiểu chuỗi
        df = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        if df.empty: return None

        # CHUẨN HÓA TÊN CỘT
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # HÀM TÌM CỘT THÔNG MINH (Dò theo nội dung thực tế bên trong ô)
        def find_col_by_content(df, keywords):
            for col in df.columns:
                # Kiểm tra 20 dòng đầu của mỗi cột xem có chứa từ khóa không
                sample = " ".join(df[col].head(20).astype(str).upper())
                if any(k in sample for k in keywords):
                    return col
            return None

        # 1. Tìm cột Mã Máy (Chứa số hiệu thiết bị)
        c_ma = find_col_by_content(df, ['3534', '1102', 'LAPTOP'])
        if not c_ma: c_ma = df.columns[1] # Mặc định cột 2

        # 2. Tìm cột Lý Do (Chứa các từ liên quan đến hỏng hóc)
        c_ly = find_col_by_content(df, ['LỖI', 'HỎNG', 'THAY', 'SỬA', 'YẾU', 'LIỆT'])
        if not c_ly: c_ly = df.columns[3] # Mặc định cột 4

        # 3. Tìm cột Ngày
        c_ng = find_col_by_content(df, ['2023', '2024', '2025', '2026', '/'])
        if not c_ng: c_ng = df.columns[6] # Mặc định cột 7

        # XỬ LÝ DỮ LIỆU SẠCH
        res_df = pd.DataFrame()
        res_df['MÃ_MÁY'] = df[c_ma].astype(str).str.split('.').str[0].str.strip()
        res_df['LÝ_DO'] = df[c_ly].astype(str).str.strip()
        res_df['NGÀY_GỐC'] = pd.to_datetime(df[c_ng], dayfirst=True, errors='coerce')
        
        # Lọc bỏ dòng tiêu đề trang trí hoặc dòng trống
        res_df = res_df[res_df['MÃ_MÁY'].str.len() > 2].copy()
        
        # Loại bỏ các dòng mà "Lý do" bị nhầm sang Tên Hãng (HP, DELL, ASUS...)
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE', 'MACBOOK']
        res_df = res_df[~res_df['LÝ_DO'].str.upper().isin(hang_may)]

        res_df['NĂM'] = res_df['NGÀY_GỐC'].dt.year.fillna(2026).astype(int)
        res_df['THÁNG'] = res_df['NGÀY_GỐC'].dt.month.fillna(1).astype(int)
        
        return res_df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ BỘ LỌC DỮ LIỆU")
    if st.button('🔄 LÀM MỚI (FOR 3.651 DÒNG)'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v57()
    if data is not None:
        st.success(f"✅ Đã kết nối {len(data)} dòng")
        
        list_năm = sorted([y for y in data['NĂM'].unique() if y > 2000], reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + list_năm)
        
        sel_month = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])
        
        df_filtered = data.copy()
        if sel_year != "Tất cả": df_filtered = df_filtered[df_filtered['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_filtered = df_filtered[df_filtered['THÁNG'] == m_num]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ QUẢN TRỊ TÀI SẢN CHI TIẾT 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # THỐNG KÊ NHANH
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Số thiết bị", df_filtered['MÃ_MÁY'].nunique())
    
    # Máy hỏng nặng (Xuất hiện > 4 lần trong dữ liệu)
    bad_list = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng nặng (>4 lần)", len(bad_list[bad_list > 4]))

    tab1, tab2 = st.tabs(["📊 BIỂU ĐỒ LỖI LINH KIỆN", "🔍 TRUY LỤC LỊCH SỬ"])
    
    with tab1:
        st.subheader("🛠️ Top 10 linh kiện/lỗi phổ biến nhất")
        # Chỉ lấy những lý do thực sự là lỗi (loại bỏ các ô trống hoặc tên hãng)
        clean_reasons = df_filtered[df_filtered['LÝ_DO'].str.len() > 3]['LÝ_DO'].value_counts().head(10)
        if not clean_reasons.empty:
            st.bar_chart(clean_reasons)
        else:
            st.info("Chưa đủ dữ liệu để vẽ biểu đồ lỗi.")

    with tab2:
        q = st.text_input("Nhập Mã máy để kiểm tra lịch sử (VD: 3534):")
        if q:
            res = data[data['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['NGÀY_GỐC', 'MÃ_MÁY', 'LÝ_DO']].sort_values('NGAY_GỐC', ascending=False), use_container_width=True)
else:
    st.info("💡 Hệ thống đang tải dữ liệu. Sếp hãy nhấn nút 'LÀM MỚI' nếu dữ liệu chưa hiện đủ 3.651 dòng.")
