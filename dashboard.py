import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN QUẢN TRỊ
st.set_page_config(page_title="Hệ Thống Quản Trị V135", layout="wide")

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v135():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            if i == 0 or "Mã số" in " ".join(row.values.astype(str)): continue
            
            # --- LẤY DỮ LIỆU THEO CỘT F (INDEX 5) ---
            ngay_goc = str(row.iloc[0]).strip()
            ma = str(row.iloc[1]).strip().split('.')[0]
            kh = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_f = str(row.iloc[5]).strip().upper() # Cột F chuẩn

            if not ma and not kh: continue

            # XỬ LÝ NGÀY THÁNG CỰC ĐOAN (ĐỂ KHÔNG MẤT DÒNG TRỐNG)
            try:
                dt = pd.to_datetime(ngay_goc, dayfirst=True, errors='coerce')
                thang = dt.month if pd.notnull(dt) else 1 # Nếu trống ngày, mặc định cho vào Tháng 1 để sếp thấy
                nam = dt.year if pd.notnull(dt) else 2026
            except:
                thang = 1
                nam = 2026

            # Chuẩn hóa nhãn vùng từ Cột F
            if "BẮC" in vung_f: v_name = "MIỀN BẮC"
            elif "TRUNG" in vung_f: v_name = "MIỀN TRUNG"
            elif "NAM" in vung_f: v_name = "MIỀN NAM"
            else: v_name = "CHƯA PHÂN LOẠI"

            # Lọc bỏ 2025 trở về trước nếu sếp muốn, còn lại giữ hết
            if nam >= 2026:
                final_rows.append([ngay_goc, nam, thang, ma, kh, lk, v_name])

        return pd.DataFrame(final_rows, columns=['NGÀY', 'NĂM', 'THÁNG', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG'])
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None

data = load_data_v135()

if data is not None:
    # Sidebar lọc
    with st.sidebar:
        st.header("⚙️ BỘ LỌC TỔNG")
        st.button('🔄 ĐỒNG BỘ DỮ LIỆU', on_click=st.cache_data.clear, use_container_width=True)
        
        sel_y = st.selectbox("Năm", ["Tất cả", 2026])
        m_list = ["Tất cả các tháng"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Tháng báo cáo", m_list)

    # Xử lý lọc dữ liệu hiển thị
    df_view = data.copy()
    if sel_y != "Tất cả": df_view = df_view[df_view['NĂM'] == sel_y]
    if sel_m != "Tất cả các tháng":
        m_num = int(sel_m.replace("Tháng ", ""))
        df_view = df_view[df_view['THÁNG'] == m_num]

    # --- HIỂN THỊ KPI GIỐNG ẢNH SẾP GỬI ---
    st.title(f"📊 Báo Cáo Tài Sản: {sel_m} - {sel_y}")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TỔNG CỘNG DỮ LIỆU", f"{len(df_view):,}")
    k2.metric("MIỀN BẮC (F)", len(df_view[df_view['VÙNG'] == 'MIỀN BẮC']))
    k3.metric("MIỀN TRUNG (F)", len(df_view[df_view['VÙNG'] == 'MIỀN TRUNG']))
    k4.metric("MIỀN NAM (F)", len(df_view[df_view['VÙNG'] == 'MIỀN NAM']))

    tab1, tab2 = st.tabs(["📉 BIỂU ĐỒ", "📋 KIỂM TRA DÒNG TRỐNG NGÀY"])
    
    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("📍 Tỷ lệ Vùng Miền (Cột F)")
            fig = px.pie(df_view, names='VÙNG', hole=0.4,
                         color_discrete_map={'MIỀN BẮC':'#0066CC', 'MIỀN TRUNG':'#FF3333', 'MIỀN NAM':'#66CCFF'})
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("🔧 Top 10 Linh kiện lỗi")
            st.bar_chart(df_view['LINH_KIỆN'].value_counts().head(10))

    with tab2:
        st.warning("Dưới đây là các dòng đang hiển thị. Nếu sếp thấy dòng nào thiếu ngày nhưng vẫn có Mã máy, hệ thống đã gom chúng vào đây để đảm bảo ĐỦ SỐ LƯỢNG.")
        st.dataframe(df_view, use_container_width=True)
