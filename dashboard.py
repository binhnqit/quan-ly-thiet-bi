import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN (HÌNH 2)
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
def load_data_v175():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        last_valid_date = None # Biến lưu trữ ngày gần nhất được tìm thấy
        
        for i, row in df_raw.iterrows():
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip().split('.')[0]
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_f = str(row.iloc[5]).strip().upper()

            if not ma_may or ma_may == "nan": continue

            # --- HÀM XỬ LÝ ĐIỀN NGÀY TỰ ĐỘNG (SMART FILL) ---
            dt_obj = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            
            if pd.notnull(dt_obj):
                last_valid_date = dt_obj # Cập nhật ngày mới nếu dòng có ghi ngày
            else:
                dt_obj = last_valid_date # Dùng lại ngày cũ nếu dòng này để trống ngày
            
            # Nếu vẫn trống (dòng đầu tiên file không có ngày), mặc định 01/01/2026
            if dt_obj is None:
                dt_obj = pd.to_datetime("01/01/2026", dayfirst=True)
            
            final_rows.append({
                "NGÀY_HIỂN_THỊ": dt_obj.strftime('%d/%m/%Y'),
                "DATE_KEY": dt_obj,
                "THÁNG": dt_obj.month,
                "NĂM": dt_obj.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": vung_f if vung_f else "CHƯA PHÂN LOẠI"
            })

        df = pd.DataFrame(final_rows)
        df['VÙNG_CHỈNH'] = df['VÙNG'].apply(lambda x: "MIỀN BẮC" if "BẮC" in x else ("MIỀN TRUNG" if "TRUNG" in x else ("MIỀN NAM" if "NAM" in x else "KHÁC/TRỐNG")))
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

data = load_data_v175()

if data is not None:
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN")
        if st.button('🔄 CẬP NHẬT LIVE DATA', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        df_2026 = data[data['NĂM'] == 2026]
        sel_m = st.selectbox("Chọn tháng báo cáo", ["Cả năm 2026"] + [f"Tháng {i}" for i in range(1, 13)])

    # Lọc dữ liệu theo tháng
    df_filtered = df_2026.copy()
    if sel_m != "Cả năm 2026":
        m_num = int(sel_m.replace("Tháng ", ""))
        df_filtered = df_filtered[df_filtered['THÁNG'] == m_num]

    # KPI SECTION
    st.markdown(f"## 📊 Báo Cáo Phân Tích Lỗi: {sel_m}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_filtered):,}")
    c2.metric("Thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    
    re_counts = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn (>1)", len(re_counts[re_counts > 1]))
    c4.metric("Khách hàng báo lỗi", df_filtered['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3 = st.tabs(["📊 XU HƯỚNG & VÙNG MIỀN", "🚩 DANH SÁCH ĐEN", "📋 DỮ LIỆU ĐỐI SOÁT"])

    with tab1:
        col_l, col_r = st.columns([1.5, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi (Đã điền ngày trống)")
            # Gom nhóm và cộng dồn các ca trong cùng một ngày
            trend = df_filtered.groupby('DATE_KEY').size().reset_index(name='Số ca')
            trend = trend.sort_values('DATE_KEY')
            fig_line = px.line(trend, x='DATE_KEY', y='Số ca', markers=True, 
                               color_discrete_sequence=['#1E3A8A'], template="plotly_white")
            st.plotly_chart(fig_line, use_container_width=True)
            
            
        with col_r:
            st.subheader("📍 Tỷ lệ Vùng Miền (Cột F)")
            fig_pie = px.pie(df_filtered, names='VÙNG_CHỈNH', hole=0.6,
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#EF4444', 'KHÁC/TRỐNG':'#CBD5E1'})
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.subheader("⚠️ Máy hỏng nhiều lần")
        bad_m = re_counts[re_counts > 1].reset_index()
        bad_m.columns = ['Mã Máy', 'Số lần']
        if not bad_m.empty:
            st.dataframe(bad_m.merge(df_filtered[['MÃ_MÁY', 'KHÁCH_HÀNG', 'VÙNG_CHỈNH']].drop_duplicates('MÃ_MÁY'), left_on='Mã Máy', right_on='MÃ_MÁY').drop(columns=['MÃ_MÁY']), use_container_width=True)

    with tab3:
        st.write("Dữ liệu sau khi điền ngày (Sếp kiểm tra cột NGÀY_HIỂN_THỊ để đối chiếu):")
        st.dataframe(df_filtered[['NGÀY_HIỂN_THỊ', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG_CHỈNH']], use_container_width=True)
