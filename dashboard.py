import streamlit as st
import pandas as pd
import plotly.express as px
import math
from datetime import datetime

# 1. CẤU HÌNH GIAO DIỆN GỐC
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border: 1px solid #e2e8f0;
        border-top: 5px solid #1E3A8A;
    }
    .main-title { color: #1E3A8A; font-weight: 800; text-align: center; font-size: 2.2rem; margin-bottom: 20px; }
    .chat-container { background-color: #f8f9fa; padding: 20px; border-radius: 15px; border: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(PUBLISHED_URL)
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"
        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0].str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except: return pd.DataFrame()

df = load_data()
current_year = 2026

# --- SIDEBAR & TẢI CSV ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    list_years = sorted(df['NĂM'].unique(), reverse=True)
    sel_year = st.selectbox("📅 Chọn Năm", list_years, index=list_years.index(current_year) if current_year in list_years else 0)
    list_vung = sorted(df['VÙNG_MIỀN'].unique())
    sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
    df_temp = df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))]
    list_months = sorted(df_temp['THÁNG'].unique())
    sel_months = st.multiselect("📆 Chọn Tháng", list_months, default=list_months)
    
    st.divider()
    if not df_temp.empty:
        csv = df_temp.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 Tải Báo Cáo CSV", data=csv, file_name=f'Bao_cao_{sel_year}.csv', mime='text/csv')

# Lọc dữ liệu chính
df_filtered = df[(df['NĂM'] == sel_year) & (df['THÁNG'].isin(sel_months)) & (df['VÙNG_MIỀN'].isin(sel_vung))]
machine_counts = df['MÃ_MÁY'].value_counts()
critical_machines = machine_counts[machine_counts >= 4].index.tolist()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<p class="main-title">🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Dashboard & AI Chat", "⚡ Ưu Tiên Mua Sắm", "📖 Hướng Dẫn"])

with tab1:
    # 3 THẺ KPI GIAO DIỆN GỐC
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    
    n_m = len(sel_months) if sel_months else 1
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    est_budget = sum([math.ceil((v/n_m)*1.2)*500000 for v in forecast_counts.values])
    c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    
    # Máy nguy kịch trong bộ lọc hiện tại
    current_critical = df_filtered[df_filtered['MÃ_MÁY'].isin(critical_machines)]['MÃ_MÁY'].nunique()
    c3.metric("Máy Nguy kịch (Đỏ)", f"{current_critical}")

    if current_critical > 0:
        st.toast(f"🚨 Có {current_critical} máy nguy kịch cần xử lý!", icon="🔥")

    st.divider()

    # --- CHATBOT AI CHIẾN LƯỢC ---
    st.subheader("💬 Trợ lý AI Phân tích Thiết bị")
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        user_input = st.text_input("Hỏi AI về mã máy (VD: 'Kiểm tra máy 3534' hoặc 'Tháng này hỏng gì nhiều nhất?')")
        
        if user_input:
            import re
            match = re.search(r'\d+', user_input)
            
            if match:
                code = match.group()
                history = df[df['MÃ_MÁY'] == code].sort_values('NGAY_FIX', ascending=False)
                if not history.empty:
                    count = len(history)
                    st.markdown(f"**AI Phản hồi:** Máy **{code}** có lịch sử hỏng **{count} lần**.")
                    if count >= 4:
                        st.error("⚠️ Lời khuyên AI: Máy này đã quá nát (Nguy kịch). KHÔNG NÊN SỬA THÊM, hãy lập biên bản thanh lý để tối ưu ngân sách.")
                    else:
                        st.info("✅ Lời khuyên AI: Tình trạng máy vẫn trong tầm kiểm soát. Ưu tiên sửa chữa linh kiện chính hãng.")
                    st.table(history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
                else:
                    st.warning(f"AI không tìm thấy dữ liệu cho máy {code}.")
            elif "hỏng gì nhiều" in user_input.lower():
                top_fail = df_filtered['LÝ_DO_HỎNG'].value_counts().idxmax()
                st.markdown(f"**AI Phản hồi:** Theo bộ lọc sếp chọn, lỗi hỏng **'{top_fail}'** đang chiếm tỷ lệ cao nhất. Sếp nên kiểm tra lại chất lượng linh kiện này hoặc cách sử dụng của nhân viên.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # THỐNG KÊ LINH KIỆN
    st.subheader("🛠️ Thống kê linh kiện hư hỏng")
    def classify_part(reason):
        reason = reason.lower()
        if 'pin' in reason: return 'Pin'
        if 'màn' in reason: return 'Màn hình'
        if 'phím' in reason: return 'Bàn phím'
        if 'nguồn' in reason or 'sạc' in reason: return 'Sạc/Nguồn'
        return 'Linh kiện khác'

    df_filtered['LINH_KIỆN'] = df_filtered['LÝ_DO_HỎNG'].apply(classify_part)
    fig_parts = px.bar(df_filtered['LINH_KIỆN'].value_counts().reset_index(), x='count', y='LINH_KIỆN', orientation='h', title="Phân loại lỗi linh kiện")
    st.plotly_chart(fig_parts, use_container_width=True)

with tab2:
    st.header("📋 Hệ Thống Ưu Tiên Mua Sắm")
    if not df_filtered.empty:
        df_p = df_filtered.copy()
        df_p['ƯU TIÊN'] = df_p.apply(lambda r: "🔴 KHẨN CẤP" if any(x in str(r['LÝ_DO_HỎNG']) for x in ['Màn', 'Main']) else "🟢 BÌNH THƯỜNG", axis=1)
        st.dataframe(df_p[['ƯU TIÊN', 'MÃ_MÁY', 'LÝ_DO_HỎNG', 'NGAY_FIX', 'VÙNG_MIỀN']], use_container_width=True)
