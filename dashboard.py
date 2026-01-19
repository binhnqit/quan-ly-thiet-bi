import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN SANG TRỌNG
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    /* Định dạng thẻ KPI theo phong cách Hình 2 */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v165():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            row_str = " ".join(row.values.astype(str))
            if i == 0 or "Mã số" in row_str: continue
            
            # Lấy dữ liệu chuẩn theo thứ tự cột
            ngay_str = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip().split('.')[0]
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_f = str(row.iloc[5]).strip().upper() # Cột F

            if not ma_may or ma_may == "nan": continue

            # Xử lý thời gian
            dt = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
            thang = dt.month if pd.notnull(dt) else 1
            nam = dt.year if pd.notnull(dt) else 2026

            # Chuẩn hóa nhãn Vùng Miền tuyệt đối từ Cột F
            if "BẮC" in vung_f: v_name = "MIỀN BẮC"
            elif "TRUNG" in vung_f: v_name = "MIỀN TRUNG"
            elif "NAM" in vung_f: v_name = "MIỀN NAM"
            else: v_name = "KHÁC/TRỐNG"

            final_rows.append([ngay_str, dt, thang, nam, ma_may, khach, lk, v_name])

        return pd.DataFrame(final_rows, columns=['NGÀY', 'DT_OBJ', 'THÁNG', 'NĂM', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG'])
    except Exception as e:
        st.error(f"Lỗi nạp liệu: {e}")
        return None

data = load_data_v165()

if data is not None:
    # SIDEBAR
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN")
        if st.button('🔄 LÀM MỚI DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        sel_y = st.selectbox("Năm", [2026, 2025])
        sel_m = st.selectbox("Tháng", ["Tất cả"] + list(range(1, 13)))

    # Lọc dữ liệu
    df_final = data[data['NĂM'] == sel_y]
    if sel_m != "Tất cả":
        df_final = df_final[df_final['THÁNG'] == sel_m]

    # --- GIAO DIỆN CHÍNH ---
    st.markdown(f"### 📊 Báo Cáo Phân Tích Lỗi - {sel_m}/{sel_y}")
    
    # KPI SECTION (NGANG - GIỐNG HÌNH 2)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng ca hỏng", len(df_final))
    k2.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    re_counts = df_final['MÃ_MÁY'].value_counts()
    re_fail_list = re_counts[re_counts > 1]
    k3.metric("Hỏng tái diễn (>1)", len(re_fail_list))
    k4.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

    st.write("---")

    # BIỂU ĐỒ XU HƯỚNG & VÙNG MIỀN
    tab1, tab2, tab3 = st.tabs(["📉 XU HƯỚNG & PHÂN BỔ", "🚩 DANH SÁCH ĐEN", "🔍 TRA CỨU"])

    with tab1:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.subheader("📈 Xu hướng lỗi theo thời gian")
            trend = df_final.groupby('NGÀY').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY', y='Số ca', markers=True, 
                               color_discrete_sequence=['#1E3A8A'], template="plotly_white")
            st.plotly_chart(fig_line, use_container_width=True)
            
            
        with c2:
            st.subheader("📍 Tỷ lệ Vùng Miền (Cột F)")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.6,
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#EF4444', 'KHÁC/TRỐNG':'#CBD5E1'})
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            

        st.subheader("🔧 Phân tích Linh kiện")
        top_lk = df_final['LINH_KIỆN'].value_counts().head(10).sort_values()
        fig_bar = px.bar(top_lk, orientation='h', color_discrete_sequence=['#1E3A8A'])
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("⚠️ Danh sách thiết bị hỏng tái diễn")
        if not re_fail_list.empty:
            rf_data = []
            for m_id, count in re_fail_list.items():
                m_info = df_final[df_final['MÃ_MÁY'] == m_id]
                rf_data.append({
                    "Mã Máy": m_id,
                    "Số lần": count,
                    "Khách hàng": m_info['KHÁCH_HÀNG'].iloc[0],
                    "Vùng": m_info['VÙNG'].iloc[0],
                    "Linh kiện lỗi": " | ".join(m_info['LINH_KIỆN'].unique())
                })
            st.dataframe(pd.DataFrame(rf_data), use_container_width=True, hide_index=True)
        else:
            st.success("Không có máy hỏng tái diễn.")

    with tab3:
        st.subheader("🔍 Truy xuất dữ liệu chi tiết")
        st.dataframe(df_final[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
