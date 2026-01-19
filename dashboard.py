import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị V125", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f1f4f9; }
    .stMetric { background: white; border-radius: 10px; padding: 20px; border-left: 5px solid #1E3A8A; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; border-radius: 10px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v125():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            row_str = " ".join(row.values.astype(str))
            if i == 0 or "Mã số" in row_str: continue
            
            # Lọc Ngày & Năm 2026
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_str)
            if not date_match: continue
            ngay_str = date_match.group(1)
            ngay_dt = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
            
            if ngay_dt is None or ngay_dt.year != 2026: continue

            # --- TRUY XUẤT THEO CỘT GỐC (F = INDEX 5) ---
            ma = str(row.iloc[1]).strip().split('.')[0]
            kh = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            # Cột F trong Excel tương ứng với index 5 trong Python
            vung_goc = str(row.iloc[5]).strip().upper() if len(row) > 5 else "CHƯA PHÂN LOẠI"
            
            # Chuẩn hóa tên vùng để biểu đồ không bị vụn
            if "BẮC" in vung_goc: vung_final = "MIỀN BẮC"
            elif "TRUNG" in vung_goc: vung_final = "MIỀN TRUNG"
            elif "NAM" in vung_goc: vung_final = "MIỀN NAM"
            else: vung_final = "KHÁC"

            if ma and ma != "nan":
                final_rows.append([ngay_str, ngay_dt, ma, kh, lk, vung_final])

        df = pd.DataFrame(final_rows, columns=['NGÀY', 'DT_OBJ', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG'])
        df['THÁNG'] = df['DT_OBJ'].dt.month
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

data = load_data_v125()

if data is not None:
    # Sidebar
    with st.sidebar:
        st.title("🛡️ QUẢN TRỊ 2026")
        if st.button('🔄 LÀM MỚI DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        m_list = ["Cả năm 2026"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Chọn thời gian", m_list)

        df_final = data.copy()
        if sel_m != "Cả năm 2026":
            df_final = df_final[df_final['THÁNG'] == int(sel_m.replace("Tháng ", ""))]

    # KPI
    st.title(f"📊 Báo Cáo Tổng Hợp 2026 - {sel_m}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Số thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    re_counts = df_final['MÃ_MÁY'].value_counts()
    re_fail = re_counts[re_counts > 1]
    c3.metric("Hỏng tái diễn", len(re_fail))
    c4.metric("Dòng dữ liệu Miền Bắc", len(df_final[df_final['VÙNG'] == 'MIỀN BẮC']))

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 THỐNG KÊ CHI TIẾT", "🚩 DANH SÁCH HỎNG TÁI DIỄN", "📋 KIỂM TRA CỘT F"])

    with tab1:
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📍 Phân bổ Vùng Miền (Theo Cột F)")
            # Biểu đồ Donut chuẩn hóa
            fig = px.pie(df_final, names='VÙNG', hole=0.5,
                         color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN TRUNG':'#F59E0B', 'MIỀN NAM':'#10B981', 'KHÁC':'#9E9E9E'})
            st.plotly_chart(fig, use_container_width=True)
            
        with col_r:
            st.subheader("🔧 Top 10 Linh kiện lỗi")
            st.bar_chart(df_final['LINH_KIỆN'].value_counts().head(10))

    with tab2:
        st.subheader("⚠️ Cảnh báo thiết bị sửa chữa nhiều lần")
        if not re_fail.empty:
            bl_rows = []
            for m_id, count in re_fail.items():
                m_info = df_final[df_final['MÃ_MÁY'] == m_id]
                bl_rows.append({
                    "Mã Máy": m_id,
                    "Số lần hỏng": count,
                    "Khách hàng": m_info['KHÁCH_HÀNG'].iloc[0],
                    "Vùng (Cột F)": m_info['VÙNG'].iloc[0],
                    "Lịch sử thay thế": " | ".join(m_info['LINH_KIỆN'].unique())
                })
            st.table(pd.DataFrame(bl_rows).sort_values("Số lần hỏng", ascending=False))
        else:
            st.success("Dữ liệu sạch: Không có máy hỏng tái diễn.")

    with tab3:
        st.write("Dưới đây là dữ liệu thực tế bóc tách từ cột F để sếp đối chiếu:")
        st.dataframe(df_final[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'VÙNG', 'LINH_KIỆN']], use_container_width=True)
