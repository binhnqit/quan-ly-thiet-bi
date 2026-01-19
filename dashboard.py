import streamlit as st
import pandas as pd
import plotly.express as px
import math
from datetime import datetime

# 1. CẤU HÌNH GIAO DIỆN (GIỮ NGUYÊN STYLE GỐC)
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { 
        background-color: #ffffff; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #1E3A8A;
    }
    .main-title { color: #1E3A8A; font-weight: 800; text-align: center; font-size: 2.2rem; margin-bottom: 20px; }
    .chat-container { background-color: #f0f2f6; padding: 25px; border-radius: 15px; border: 2px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU & CHUẨN HÓA
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(PUBLISHED_URL)
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        def clean_code(val):
            if pd.isna(val): return ""
            return str(val).split('.')[0].strip()
        df['MÃ_MÁY'] = df['COL_1'].apply(clean_code)
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"
        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ").astype(str).str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except: return pd.DataFrame()

df_global = load_data()

# --- SIDEBAR (MẶC ĐỊNH 2026) ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if not df_global.empty:
        list_years = sorted(df_global['NĂM'].unique(), reverse=True)
        # Ép bộ lọc về năm hiện tại 2026
        current_year = 2026
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=list_years.index(current_year) if current_year in list_years else 0)
        list_vung = sorted(df_global['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        df_filtered = df_global[(df_global['NĂM'] == sel_year) & (df_global['VÙNG_MIỀN'].isin(sel_vung))]
        
        st.divider()
        csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 Tải Báo Cáo CSV", data=csv, file_name=f'Bao_cao_{sel_year}.csv', mime='text/csv')
    else:
        df_filtered = pd.DataFrame()

# 3. XỬ LÝ DỮ LIỆU BỆNH NỀN & SORT
if not df_global.empty:
    agg_func = {
        'LÝ_DO_HỎNG': [('Số Lần Hỏng', 'count'), 
                      ('Lỗi Hay Gặp Nhất', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa lỗi")],
        'VÙNG_MIỀN': [('Vị Trí', 'first')]
    }
    machine_report = df_global.groupby('MÃ_MÁY').agg(agg_func)
    machine_report.columns = machine_report.columns.get_level_values(1)
    machine_report = machine_report.reset_index()
    # Danh sách máy nguy kịch (hỏng >= 4 lần)
    critical_data = machine_report[machine_report['Số Lần Hỏng'] >= 4].sort_values(by='Số Lần Hỏng', ascending=False)
else:
    critical_data = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<p class="main-title">🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI</p>', unsafe_allow_html=True)

tab1, tab2, tab4, tab3 = st.tabs(["📊 Dashboard & AI Chat", "⚡ Ưu Tiên Mua Sắm", "🚩 Phân Tích Bệnh Lý", "📖 Hướng Dẫn"])

with tab1:
    # 3 THẺ KPI ĐẶC TRƯNG
    c1, c2, c3 = st.columns(3)
    if not df_filtered.empty:
        c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
        forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
        est_budget = sum([math.ceil((v/1)*1.2)*500000 for v in forecast_counts.values])
        c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
        # Máy nguy kịch xuất hiện trong bộ lọc hiện tại
        curr_crit_ids = df_filtered[df_filtered['MÃ_MÁY'].isin(critical_data['MÃ_MÁY'])]['MÃ_MÁY'].nunique()
        c3.metric("Máy Nguy kịch (Đỏ)", f"{curr_crit_ids}")

    st.divider()
    col_l, col_r = st.columns(2)
    if not df_filtered.empty:
        with col_l:
            st.subheader("📍 Tỷ lệ hỏng theo Vùng miền")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5), use_container_width=True)
        with col_r:
            st.subheader("🛠️ Thống kê linh kiện")
            df_filtered['LK'] = df_filtered['LÝ_DO_HỎNG'].apply(lambda r: 'Pin' if 'pin' in r.lower() else ('Màn hình' if 'màn' in r.lower() else 'Khác'))
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h'), use_container_width=True)

    st.divider()
    # CHATBOT AI QUÉT SÂU 3.976 DÒNG
    st.subheader("💬 Trợ lý AI (Tra cứu bệnh án)")
    q = st.text_input("Gõ mã máy để AI kiểm tra (VD: 3534):")
    if q:
        import re
        m = re.search(r'\d+', q)
        if m:
            code = m.group()
            res = df_global[df_global['MÃ_MÁY'] == code].sort_values('NGAY_FIX', ascending=False)
            if not res.empty:
                st.info(f"AI: Máy {code} hỏng {len(res)} lần. " + ("**DỪNG SỬA - THANH LÝ!**" if len(res)>=4 else "**TIẾP TỤC DÙNG**"))
                st.table(res[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])

with tab2:
    st.header("📋 Ưu Tiên Mua Sắm Khẩn Cấp")
    if not df_filtered.empty:
        df_p = df_filtered.copy()
        df_p['ƯU TIÊN'] = df_p.apply(lambda r: "🔴 KHẨN CẤP" if any(x in str(r['LÝ_DO_HỎNG']) for x in ['Màn', 'Main', 'Nguồn']) else "🟢 BÌNH THƯỜNG", axis=1)
        st.dataframe(df_p[['ƯU TIÊN', 'MÃ_MÁY', 'LÝ_DO_HỎNG', 'NGAY_FIX', 'VÙNG_MIỀN']], use_container_width=True)

with tab4:
    st.header("🚩 Phân Tích Thiết Bị 'Bệnh Nền' Nặng")
    st.write("Sếp có thể nhấn vào các cột để sắp xếp (Sort) theo nhu cầu xử lý.")
    if not critical_data.empty:
        st.dataframe(
            critical_data,
            use_container_width=True,
            column_config={
                "MÃ_MÁY": "Mã Máy",
                "Số Lần Hỏng": st.column_config.NumberColumn("Số Lần Hỏng", format="%d ⚠️"),
                "Lỗi Hay Gặp Nhất": "Triệu chứng phổ biến nhất",
                "Vị Trí": "Chi nhánh quản lý"
            },
            hide_index=True
        )
    st.success("💡 Gợi ý: Hãy dựa vào cột 'Lỗi Hay Gặp Nhất' để xác định xem lỗi do phần cứng hay do thao tác người dùng.")

with tab3:
    st.markdown("""
    ### 📖 HƯỚNG DẪN VẬN HÀNH CHIẾN LƯỢC 2026
    1. **Theo dõi KPI:** Thẻ 'Máy Nguy kịch' báo đỏ là lúc sếp cần sang Tab 4.
    2. **Duyệt thanh lý:** Tại Tab 4, sếp dùng chức năng Sort để lọc máy hỏng nhiều nhất.
    3. **Tra cứu nhanh:** Chatbot AI giúp kỹ thuật viên biết máy có 'đáng' để sửa tiếp hay không.
    """)
