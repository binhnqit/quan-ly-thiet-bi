import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# 1. THIẾT LẬP GIAO DIỆN EXECUTIVE
st.set_page_config(page_title="Hệ Thống Quản Trị V120 - 2026", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background: white; border-radius: 12px; padding: 20px; border-top: 5px solid #1E3A8A; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; padding: 10px; border-radius: 10px; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_2026_only():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        cleaned_rows = []
        for i, row in df_raw.iterrows():
            row_str = " ".join(row.values.astype(str))
            # Bỏ qua dòng tiêu đề
            if i == 0 or "Mã số" in row_str: continue
            
            # 1. BÓC TÁCH NGÀY THÁNG
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_str)
            if not date_match: continue
            ngay_str = date_match.group(1)
            ngay_dt = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
            
            # --- BỘ LỌC CỨNG 2026 ---
            if ngay_dt is None or ngay_dt.year != 2026:
                continue # Bỏ qua dữ liệu 2025 trở về trước

            # 2. LẤY DỮ LIỆU CHUẨN (Theo index sếp đã xác nhận ở V101)
            ma = str(row.iloc[1]).strip().split('.')[0]
            kh = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            
            # 3. PHÂN VÙNG MIỀN THÔNG MINH (Bao gồm tên đơn vị Miền Trung sếp đã nêu)
            def identify_vung(khach):
                v = str(khach).upper()
                trung_keywords = [
                    'ĐÀ NẴNG', 'HUẾ', 'VINH', 'NGHỆ', 'TĨNH', 'QUẢNG', 'BÌNH ĐỊNH', 
                    'KHÁNH HÒA', 'NHA TRANG', 'PHÚ NGUYỄN', 'NGỌC VĨNH', 'PHÚC LỘC THỌ'
                ]
                bac_keywords = ['HN', 'NỘI', 'BẮC', 'SƠN', 'PHÚ THỌ', 'THÁI NGUYÊN', 'GIANG', 'NINH']
                
                if any(x in v for x in trung_keywords): return 'MIỀN TRUNG'
                if any(x in v for x in bac_keywords): return 'MIỀN BẮC'
                return 'MIỀN NAM'

            vung = identify_vung(kh)
            
            if ma and ma != "nan":
                cleaned_rows.append([ngay_str, ngay_dt, ma, kh, lk, vung])

        df = pd.DataFrame(cleaned_rows, columns=['NGÀY', 'DT_OBJ', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG'])
        df['THÁNG'] = df['DT_OBJ'].dt.month
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- GIAO DIỆN CHÍNH ---
data = load_data_2026_only()

if data is not None:
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN 2026")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU MỚI', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        m_list = ["Tất cả năm 2026"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Chọn kỳ báo cáo", m_list)

        df_final = data.copy()
        if sel_m != "Tất cả năm 2026":
            df_final = df_final[df_final['THÁNG'] == int(sel_m.replace("Tháng ", ""))]

    # --- HIỂN THỊ KPI ---
    st.title(f"📊 Báo Cáo Tài Sản 2026 - {sel_m}")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng ca hỏng (2026)", len(df_final))
    k2.metric("Số thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    # Tính máy hỏng tái diễn
    re_counts = df_final['MÃ_MÁY'].value_counts()
    re_fail = re_counts[re_counts > 1]
    k3.metric("Máy hỏng tái diễn", len(re_fail))
    
    # Miền trung
    trung_count = len(df_final[df_final['VÙNG'] == 'MIỀN TRUNG'])
    k4.metric("Dữ liệu Miền Trung", trung_count)

    tab1, tab2, tab3 = st.tabs(["📉 BIỂU ĐỒ TỔNG QUAN", "⚠️ DANH SÁCH ĐEN", "📋 DỮ LIỆU ĐỐI SOÁT"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📍 Tỷ trọng Vùng Miền (Chuẩn 2026)")
            fig = px.pie(df_final, names='VÙNG', hole=0.5,
                         color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN TRUNG':'#F59E0B', 'MIỀN NAM':'#10B981'})
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("🔧 Top 10 Linh kiện lỗi")
            top_lk = df_final['LINH_KIỆN'].value_counts().head(10)
            st.bar_chart(top_lk)

    with tab2:
        st.subheader("🚩 THIẾT BỊ HỎNG TRÊN 1 LẦN (NĂM 2026)")
        if not re_fail.empty:
            bl_rows = []
            for m_id, count in re_fail.items():
                m_info = df_final[df_final['MÃ_MÁY'] == m_id]
                bl_rows.append({
                    "Mã Máy": m_id,
                    "Số lần hỏng": count,
                    "Khách hàng": m_info['KHÁCH_HÀNG'].iloc[0],
                    "Vùng": m_info['VÙNG'].iloc[0],
                    "Các linh kiện lỗi": " | ".join(m_info['LINH_KIỆN'].unique())
                })
            st.table(pd.DataFrame(bl_rows).sort_values("Số lần hỏng", ascending=False))
        else:
            st.success("Không có máy hỏng tái diễn trong dữ liệu 2026.")

    with tab3:
        st.write("Dữ liệu 2026 đã được lọc sạch hoàn toàn:")
        st.dataframe(df_final[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
