import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. GIAO DIỆN CHUẨN (HÌNH 2)
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi 2026", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    div[data-testid="stMetric"] {
        background-color: white; border-radius: 10px; padding: 15px;
        border-left: 5px solid #1E3A8A; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v190():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        # BIẾN LƯU NGÀY HIỆN TẠI (Dùng cho logic tiếp diễn của sếp)
        active_date = pd.to_datetime("01/01/2026", dayfirst=True) 
        
        for i, row in df_raw.iterrows():
            # Bỏ qua dòng tiêu đề và dòng không có mã máy (cột B)
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_f = str(row.iloc[5]).strip().upper()

            # --- BƯỚC 1: CHẶN DÒNG TRỐNG (TRÁNH SỐ ẢO) ---
            if not ma_may or ma_may.lower() in ["nan", ""]:
                continue 

            # --- BƯỚC 2: LOGIC NGÀY TIẾP DIỄN CỦA SẾP ---
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse):
                active_date = dt_parse # Nếu dòng có ngày mới, cập nhật ngay
            
            # Gán ngày (dù dòng đó trống ngày nhưng có mã máy, nó sẽ lấy active_date)
            final_rows.append({
                "NGÀY_GỐC": final_dt.strftime('%d/%m/%Y'),
                "DATE_KEY": active_date,
                "THÁNG": active_date.month,
                "NĂM": active_date.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": vung_f
            })

        df = pd.DataFrame(final_rows)
        # Chuẩn hóa Vùng Miền để biểu đồ Donut khớp Hình 2
        df['VÙNG_CHỈNH'] = df['VÙNG'].apply(lambda x: "MIỀN BẮC" if "BẮC" in x else ("MIỀN TRUNG" if "TRUNG" in x else ("MIỀN NAM" if "NAM" in x else "KHÁC/TRỐNG")))
        return df
    except Exception as e:
        return None

data = load_data_v185() # Gọi hàm nạp liệu

if data is not None:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ 2026")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Lọc theo năm và tháng
        list_thang = ["Cả năm 2026"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Chọn kỳ báo cáo", list_thang)

    # Thực hiện lọc
    df_2026 = data[data['NĂM'] == 2026]
    if sel_m == "Cả năm 2026":
        df_filtered = df_2026
    else:
        m_num = int(sel_m.replace("Tháng ", ""))
        df_filtered = df_2026[df_2026['THÁNG'] == m_num]

    # --- HIỂN THỊ KPI ---
    st.markdown(f"## 📊 Báo Cáo Tài Sản: {sel_m}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
    c2.metric("Số thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    
    re_counts = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn (>1)", len(re_counts[re_counts > 1]))
    c4.metric("Khách hàng báo lỗi", df_filtered['KHÁCH_HÀNG'].nunique())

    # --- BIỂU ĐỒ ---
    tab1, tab2 = st.tabs(["📊 XU HƯỚNG & VÙNG MIỀN", "🔍 TRA CỨU CHI TIẾT"])
    
    with tab1:
        col_l, col_r = st.columns([1.5, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi (Dữ liệu cộng dồn ngày)")
            # Gom nhóm theo ngày để vẽ biểu đồ đường chuẩn
            trend = df_filtered.groupby('DATE_KEY').size().reset_index(name='Số ca')
            fig_line = px.line(trend.sort_values('DATE_KEY'), x='DATE_KEY', y='Số ca', markers=True, color_discrete_sequence=['#1E3A8A'])
            st.plotly_chart(fig_line, use_container_width=True)
                        
        with col_r:
            st.subheader("📍 Tỷ lệ Vùng Miền (Cột F)")
            fig_pie = px.pie(df_filtered, names='VÙNG_CHỈNH', hole=0.6, 
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#EF4444'})
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.subheader("📋 Dữ liệu sau khi xử lý tiếp diễn")
        st.dataframe(df_filtered[['NGÀY_GỐC', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG_CHỈNH']], use_container_width=True)
