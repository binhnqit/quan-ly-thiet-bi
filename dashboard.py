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

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    list_years = sorted(df_global['NĂM'].unique(), reverse=True)
    sel_year = st.selectbox("📅 Chọn Năm", list_years, index=list_years.index(2026) if 2026 in list_years else 0)
    list_vung = sorted(df_global['VÙNG_MIỀN'].unique())
    sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
    df_filtered = df_global[(df_global['NĂM'] == sel_year) & (df_global['VÙNG_MIỀN'].isin(sel_vung))]

# 3. XỬ LÝ DỮ LIỆU MÁY HỎNG NHIỀU (Dùng cho Tab 4 và KPI)
machine_stats = df_global['MÃ_MÁY'].value_counts().reset_index()
machine_stats.columns = ['Mã Máy', 'Số Lần Hỏng']
# Lọc những máy hỏng >= 4 lần
critical_list = machine_stats[machine_stats['Số Lần Hỏng'] >= 4]

# --- GIAO DIỆN CHÍNH ---
st.markdown('<p class="main-title">🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI</p>', unsafe_allow_html=True)

tab1, tab2, tab4, tab3 = st.tabs(["📊 Dashboard & AI Chat", "⚡ Ưu Tiên Mua Sắm", "🚩 Danh Sách Nguy Kịch", "📖 Hướng Dẫn"])

with tab1:
    # 3 THẺ KPI GỐC
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    est_budget = sum([math.ceil((v/1)*1.2)*500000 for v in forecast_counts.values])
    c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    
    # Chỉ tính máy nguy kịch xuất hiện trong dữ liệu đang lọc
    curr_crit = df_filtered[df_filtered['MÃ_MÁY'].isin(critical_list['Mã Máy'])]['MÃ_MÁY'].nunique()
    c3.metric("Máy Nguy kịch (Đỏ)", f"{curr_crit}")

    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ hỏng theo Vùng miền")
        st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5), use_container_width=True)
    with col_r:
        st.subheader("🛠️ Thống kê linh kiện")
        def classify(r):
            r = r.lower()
            if 'pin' in r: return 'Pin'; 
            if 'màn' in r: return 'Màn hình'
            return 'Khác'
        df_filtered['LK'] = df_filtered['LÝ_DO_HỎNG'].apply(classify)
        st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h'), use_container_width=True)

    # CHATBOT AI (V14)
    st.divider()
    st.subheader("💬 Trợ lý AI (Tra cứu bệnh án)")
    q = st.text_input("Gõ mã máy (VD: 3534):", key="chatbot_input")
    if q:
        import re
        m = re.search(r'\d+', q)
        if m:
            code = m.group()
            res = df_global[df_global['MÃ_MÁY'] == code].sort_values('NGAY_FIX', ascending=False)
            if not res.empty:
                st.info(f"AI: Máy {code} hỏng {len(res)} lần. " + ("**ĐỀ XUẤT THANH LÝ!**" if len(res)>=4 else "**SỬA TIẾP**"))
                st.dataframe(res[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']], use_container_width=True)

with tab2:
    st.header("📋 Ưu Tiên Mua Sắm")
    df_p = df_filtered.copy()
    df_p['ƯU TIÊN'] = df_p.apply(lambda r: "🔴 KHẨN CẤP" if any(x in str(r['LÝ_DO_HỎNG']) for x in ['Màn', 'Main']) else "🟢 BÌNH THƯỜNG", axis=1)
    st.dataframe(df_p[['ƯU TIÊN', 'MÃ_MÁY', 'LÝ_DO_HỎNG', 'NGAY_FIX', 'VÙNG_MIỀN']], use_container_width=True)

with tab4:
    st.header("🚩 Phân Tích Thiết Bị Hỏng Nhiều Lần")
    st.write("Dưới đây là danh sách các máy hỏng từ **4 lần trở lên** (Toàn thời gian). Sếp có thể nhấn vào tiêu đề cột để sắp xếp.")
    
    # Bổ sung thông tin Vùng miền cho danh sách nguy kịch để sếp dễ xử lý
    last_known_region = df_global.drop_duplicates('MÃ_MÁY', keep='first')[['MÃ_MÁY', 'VÙNG_MIỀN']]
    critical_data = critical_list.merge(last_known_region, left_on='Mã Máy', right_on='MÃ_MÁY').drop(columns=['MÃ_MÁY'])
    
    # Hiển thị bảng với chức năng SORT mặc định của Streamlit
    st.dataframe(
        critical_data.sort_values(by='Số Lần Hỏng', ascending=False),
        use_container_width=True,
        column_config={
            "Số Lần Hỏng": st.column_config.NumberColumn(format="%d 🔥"),
            "Mã Máy": st.column_config.TextColumn("Mã Máy Thiết Bị"),
            "VÙNG_MIỀN": "Vị Trí Gần Nhất"
        }
    )
    
    st.warning("💡 **Hướng xử lý:** Các máy có biểu tượng 🔥 nhiều nên được đưa vào diện thanh lý trong quý này.")

with tab3:
    st.info("### 📖 Hướng Dẫn Vận Hành\n1. Tab 1: Xem tổng quan và Chat với AI.\n2. Tab 2: Xem linh kiện cần mua gấp.\n3. Tab 4: Lọc máy nát để lập danh sách thanh lý.")
