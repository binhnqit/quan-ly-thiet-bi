import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị V130", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f1f4f9; }
    .stMetric { background: white; border-radius: 10px; padding: 20px; border-left: 5px solid #1E3A8A; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v130():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc toàn bộ file, không bỏ sót dòng nào
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            # Bỏ qua dòng tiêu đề nếu chứa chữ "Mã số"
            row_str = " ".join(row.values.astype(str))
            if i == 0 or "Mã số" in row_str: continue
            
            # --- TRUY XUẤT DỮ LIỆU ---
            # Cột A: Ngày | Cột B: Mã máy | Cột C: Khách | Cột D: Linh kiện | Cột F: Vùng (Index 5)
            ngay_str = str(row.iloc[0]).strip()
            ma = str(row.iloc[1]).strip().split('.')[0]
            kh = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper() if len(row) > 5 else ""

            # Chỉ bỏ qua nếu dòng trắng hoàn toàn
            if not ma and not kh: continue

            # Xử lý Ngày để lọc năm 2026
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', ngay_str)
            if date_match:
                dt_obj = pd.to_datetime(date_match.group(1), dayfirst=True, errors='coerce')
                nam = dt_obj.year if pd.notnull(dt_obj) else 2026
                thang = dt_obj.month if pd.notnull(dt_obj) else 0
            else:
                nam = 2026 # Mặc định là 2026 nếu không rõ ngày để tránh mất dữ liệu
                thang = 0

            # Chuẩn hóa Vùng từ cột F
            if "BẮC" in vung_raw: v_final = "MIỀN BẮC"
            elif "TRUNG" in vung_raw: v_final = "MIỀN TRUNG"
            elif "NAM" in vung_raw: v_final = "MIỀN NAM"
            else: v_final = "KHÁC/CHƯA GHI"

            final_rows.append([ngay_str, nam, thang, ma, kh, lk, v_final])

        df = pd.DataFrame(final_rows, columns=['NGÀY', 'NĂM', 'THÁNG', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG'])
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

data = load_data_v130()

if data is not None:
    with st.sidebar:
        st.title("🛡️ QUẢN TRỊ TỔNG QUÁT")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Cho phép sếp chọn "Tất cả" để không mất bất kỳ dòng nào
        list_nam = ["Tất cả dữ liệu"] + sorted([str(int(x)) for x in data['NĂM'].unique() if x > 0], reverse=True)
        sel_y = st.selectbox("Lọc theo Năm", list_nam)
        
        list_thang = ["Tất cả các tháng"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Lọc theo Tháng", list_thang)

        df_final = data.copy()
        if sel_y != "Tất cả dữ liệu":
            df_final = df_final[df_final['NĂM'] == int(sel_y)]
        if sel_m != "Tất cả các tháng":
            df_final = df_final[df_final['THÁNG'] == int(sel_m.replace("Tháng ", ""))]

    # --- HIỂN THỊ ---
    st.title(f"📊 Báo Cáo Tài Sản: {sel_m} - {sel_y}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TỔNG CỘNG DỮ LIỆU", f"{len(df_final):,}")
    c2.metric("MIỀN BẮC (F)", len(df_final[df_final['VÙNG'] == 'MIỀN BẮC']))
    c3.metric("MIỀN TRUNG (F)", len(df_final[df_final['VÙNG'] == 'MIỀN TRUNG']))
    c4.metric("MIỀN NAM (F)", len(df_final[df_final['VÙNG'] == 'MIỀN NAM']))

    t1, t2, t3 = st.tabs(["📈 BIỂU ĐỒ TỔNG KẾT", "⚠️ DANH SÁCH HỎNG TÁI DIỄN", "🔍 TRA CỨU CHI TIẾT"])

    with t1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📍 Tỷ lệ Vùng Miền (Cột F)")
            # Vẽ biểu đồ tròn dựa trên cột F
            fig = px.pie(df_final, names='VÙNG', hole=0.4,
                         color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN TRUNG':'#F59E0B', 'MIỀN NAM':'#10B981', 'KHÁC/CHƯA GHI':'#9E9E9E'})
            st.plotly_chart(fig, use_container_width=True)
            
        with col_b:
            st.subheader("🔧 Top 10 Linh kiện lỗi")
            st.bar_chart(df_final['LINH_KIỆN'].value_counts().head(10))

    with t2:
        re_counts = df_final['MÃ_MÁY'].value_counts()
        re_fail = re_counts[re_counts > 1]
        st.subheader(f"🚩 Có {len(re_fail)} thiết bị hỏng trên 1 lần")
        if not re_fail.empty:
            bl_rows = []
            for m_id, count in re_fail.items():
                if not m_id or m_id == "nan": continue
                m_info = df_final[df_final['MÃ_MÁY'] == m_id]
                bl_rows.append({
                    "Mã Máy": m_id,
                    "Số lần": count,
                    "Đơn vị": m_info['KHÁCH_HÀNG'].iloc[0],
                    "Vùng": m_info['VÙNG'].iloc[0],
                    "Lỗi": " | ".join(m_info['LINH_KIỆN'].unique())
                })
            st.dataframe(pd.DataFrame(bl_rows), use_container_width=True)

    with t3:
        st.write("Dữ liệu chi tiết (Đối soát trực tiếp với Google Sheets):")
        st.dataframe(df_final, use_container_width=True)
