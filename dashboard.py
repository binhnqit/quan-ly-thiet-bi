import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN EXECUTIVE (GIỐNG HÌNH 2)
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { background: white; border-radius: 12px; padding: 15px; border-bottom: 4px solid #1E3A8A; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v160():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_str = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip().split('.')[0]
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper() # Cột F

            if not ma_may or ma_may == "nan": continue

            # Logic nhận diện ngày tháng thông minh
            dt = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
            
            # Gán giá trị mặc định nếu ngày lỗi để không mất dữ liệu
            thang = dt.month if pd.notnull(dt) else 1
            nam = dt.year if pd.notnull(dt) else 2026
            ngay_dt = dt if pd.notnull(dt) else pd.to_datetime("2026-01-01")

            # Chuẩn hóa vùng miền theo cột F
            if "BẮC" in vung_raw: v_final = "MIỀN BẮC"
            elif "TRUNG" in vung_raw: v_final = "MIỀN TRUNG"
            elif "NAM" in vung_raw: v_final = "MIỀN NAM"
            else: v_final = "KHÁC/TRỐNG"

            final_rows.append({
                "NGÀY_GỐC": ngay_str,
                "NGÀY_DT": ngay_dt,
                "THÁNG": thang,
                "NĂM": nam,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": v_final
            })

        return pd.DataFrame(final_rows)
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

data = load_data_v160()

if data is not None:
    # --- SIDEBAR (GIỐNG HÌNH 2) ---
    with st.sidebar:
        st.header("🛡️ QUẢN TRỊ V160")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_y = st.selectbox("Chọn Năm", sorted(data['NĂM'].unique(), reverse=True))
        sel_m = st.selectbox("Chọn Tháng", ["Tất cả"] + list(range(1, 13)))

    # Lọc dữ liệu chuẩn cho 2026
    df_filtered = data[data['NĂM'] == sel_y]
    if sel_m != "Tất cả":
        df_filtered = df_filtered[df_filtered['THÁNG'] == sel_m]

    # --- TIÊU ĐỀ (GIỐNG HÌNH 2) ---
    st.markdown(f"## 📊 Hệ Thống Phân Tích Lỗi Thiết Bị - {sel_m}/{sel_y}")

    # --- KPI CARDS (HÌNH 2) ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    
    re_counts = df_filtered['MÃ_MÁY'].value_counts()
    re_fail = len(re_counts[re_counts > 1])
    c3.metric("Hỏng tái diễn (>1 lần)", re_fail)
    c4.metric("Khách hàng báo lỗi", df_filtered['KHÁCH_HÀNG'].nunique())

    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 XU HƯỚNG & PHÂN BỔ", "🚩 QUẢN TRỊ RỦI RO (RE-FAIL)", "🔍 TRUY XUẤT NHANH", "📋 DỮ LIỆU GỐC"])

    with tab1:
        col_l, col_r = st.columns([1.5, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi theo thời gian")
            df_trend = df_filtered.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(df_trend, x='NGÀY_DT', y='Số ca', markers=True, 
                               line_shape="spline", color_discrete_sequence=['#1E3A8A'])
            st.plotly_chart(fig_line, use_container_width=True)
            
        with col_r:
            st.subheader("📍 Phân bổ Vùng Miền (Cột F)")
            fig_pie = px.pie(df_filtered, names='VÙNG', hole=0.6,
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#EF4444', 'KHÁC/TRỐNG':'#94A3B8'})
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("🔧 Phân tích Linh kiện lỗi")
        fig_bar = px.bar(df_filtered['LINH_KIỆN'].value_counts().head(15), orientation='h', 
                         color_discrete_sequence=['#1E3A8A'])
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("⚠️ DANH SÁCH MÁY HỎNG TRÊN
