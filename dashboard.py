import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. THIẾT LẬP GIAO DIỆN CHUẨN (GIỐNG HÌNH 2)
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản - 2026", layout="wide")

st.markdown("""
    <style>
    /* Nền và font chữ */
    .main { background-color: #f4f7f9; }
    /* Style cho các thẻ KPI giống hình sếp gửi */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 4px solid #1E3A8A;
        text-align: center;
    }
    .metric-title { font-size: 16px; color: #666; margin-bottom: 10px; }
    .metric-value { font-size: 32px; font-weight: bold; color: #1E3A8A; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v150():
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
            vung_raw = str(row.iloc[5]).strip().upper()

            if not ma_may or ma_may == "nan": continue

            # Xử lý ngày tháng 2026
            dt = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
            if pd.notnull(dt) and dt.year == 2026:
                # Chuẩn hóa Vùng Miền tuyệt đối theo Cột F
                if "BẮC" in vung_raw: v_final = "MIỀN BẮC"
                elif "TRUNG" in vung_raw: v_final = "MIỀN TRUNG"
                elif "NAM" in vung_raw: v_final = "MIỀN NAM"
                else: v_final = "KHÁC"

                final_rows.append([ngay_str, dt.month, ma_may, khach, lk, v_final])

        return pd.DataFrame(final_rows, columns=['NGÀY', 'THÁNG', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG'])
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None

data = load_data_v150()

if data is not None:
    # --- SIDEBAR ĐIỀU KHIỂN ---
    with st.sidebar:
        st.markdown("### ⚙️ QUẢN TRỊ V150")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU MỚI', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_m = st.selectbox("Chọn kỳ báo cáo", ["Tất cả/2026"] + [f"Tháng {i}" for i in range(1, 13)])

    # Lọc dữ liệu
    df_filtered = data.copy()
    if sel_m != "Tất cả/2026":
        df_filtered = df_filtered[df_filtered['THÁNG'] == int(sel_m.replace("Tháng ", ""))]

    # --- TIÊU ĐỀ ---
    st.title(f"📊 Báo Cáo Tài Sản: {sel_m}")

    # --- KHỐI KPI (DESIGN GIỐNG HÌNH 2) ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Tổng ca hỏng</div><div class="metric-value">{len(df_filtered)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Thiết bị lỗi</div><div class="metric-value">{df_filtered["MÃ_MÁY"].nunique()}</div></div>', unsafe_allow_html=True)
    with c3:
        re_fail_count = len(df_filtered['MÃ_MÁY'].value_counts()[df_filtered['MÃ_MÁY'].value_counts() > 1])
        st.markdown(f'<div class="metric-card"><div class="metric-title">Hỏng tái diễn (>1 lần)</div><div class="metric-value">{re_fail_count}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Tỷ lệ khắc phục</div><div class="metric-value">100%</div></div>', unsafe_allow_html=True)

    st.write("---")

    # --- KHỐI BIỂU ĐỒ ---
    t1, t2, t3 = st.tabs(["📊 XU HƯỚNG & PHÂN BỔ", "🚩 DANH SÁCH ĐEN", "📋 DỮ LIỆU SẠCH"])

    with t1:
        col_left, col_right = st.columns([1, 1.2])
        with col_left:
            st.subheader("📍 Phân bổ Vùng Miền")
            fig_pie = px.pie(df_filtered, names='VÙNG', hole=0.6,
                             color='VÙNG', color_discrete_map={'MIỀN BẮC':'#004AAD', 'MIỀN TRUNG':'#FF4B4B', 'MIỀN NAM':'#00D26A'})
            fig_pie.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_right:
            st.subheader("🔧 Top Linh kiện hỏng")
