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
        border-top: 5px solid #1E3A8A;
    }
    .main-title { color: #1E3A8A; font-weight: 800; text-align: center; font-size: 2.2rem; margin-bottom: 20px; }
    .chat-container { background-color: #f0f2f6; padding: 25px; border-radius: 15px; border: 2px solid #1E3A8A; }
    .guide-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid #1E3A8A; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU & CHUẨN HÓA MÃ MÁY
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(PUBLISHED_URL)
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # Hàm chuẩn hóa mã máy để Chatbot đọc không bao giờ sai
        def clean_machine_code(val):
            if pd.isna(val): return ""
            # Chuyển 3534.0 -> 3534
            s = str(val).split('.')[0].strip()
            return s

        df['MÃ_MÁY'] = df['COL_1'].apply(clean_machine_code)
        
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

# --- BỘ LỌC CHIẾN LƯỢC ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if not df_global.empty:
        list_years = sorted(df_global['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=list_years.index(2026) if 2026 in list_years else 0)
        list_vung = sorted(df_global['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        df_temp = df_global[(df_global['NĂM'] == sel_year) & (df_global['VÙNG_MIỀN'].isin(sel_vung))]
        list_months = sorted(df_temp['THÁNG'].unique())
        sel_months = st.multiselect("📆 Chọn Tháng", list_months, default=list_months)
        
        st.divider()
        csv = df_temp.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 Tải Báo Cáo CSV", data=csv, file_name=f'Bao_cao_{sel_year}.csv', mime='text/csv')

df_filtered = df_global[(df_global['NĂM'] == sel_year) & (df_global['THÁNG'].isin(sel_months)) & (df_global['VÙNG_MIỀN'].isin(sel_vung))]
machine_counts = df_global['MÃ_MÁY'].value_counts()
critical_machines = machine_counts[machine_counts >= 4].index.tolist()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<p class="main-title">🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Dashboard & AI Chat", "⚡ Ưu Tiên Mua Sắm", "📖 Hướng Dẫn"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    
    n_m = len(sel_months) if sel_months else 1
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    est_budget = sum([math.ceil((v/n_m)*1.2)*500000 for v in forecast_counts.values])
    c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    
    curr_crit_count = df_filtered[df_filtered['MÃ_MÁY'].isin(critical_machines)]['MÃ_MÁY'].nunique()
    c3.metric("Máy Nguy kịch (Đỏ)", f"{curr_crit_count}")

    st.divider()

    # BIỂU ĐỒ TRÒN & LINH KIỆN
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ hỏng theo Vùng miền")
        st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5), use_container_width=True)
    with col_r:
        st.subheader("🛠️ Thống kê linh kiện")
        def classify(r):
            r = r.lower()
            if 'pin' in r: return 'Pin'
            if 'màn' in r: return 'Màn hình'
            if 'phím' in r: return 'Bàn phím'
            return 'Linh kiện khác'
        df_filtered['LK'] = df_filtered['LÝ_DO_HỎNG'].apply(classify)
        st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h'), use_container_width=True)

    st.divider()

    # --- CHATBOT AI QUÉT DỮ LIỆU ĐÃ ĐƯỢC CHUẨN HÓA ---
    st.subheader("💬 Trợ lý AI (Tra cứu bệnh án máy)")
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        q = st.text_input("Gõ mã máy để AI quét dữ liệu (VD: 3534):")
        if q:
            # Tách lấy phần số từ câu hỏi của sếp
            import re
            m = re.search(r'\d+', q)
            if m:
                target_code = m.group()
                # Quét trên toàn bộ 3.976 dòng đã chuẩn hóa
                res = df_global[df_global['MÃ_MÁY'] == target_code].sort_values('NGAY_FIX', ascending=False)
                
                if not res.empty:
                    count = len(res)
                    st.markdown(f"✅ **AI tìm thấy:** Máy **{target_code}** hỏng **{count} lần**.")
                    if count >= 4:
                        st.error(f"🚨 CẢNH BÁO: Máy {target_code} nằm trong danh sách ĐỎ. Đề xuất THANH LÝ NGAY.")
                    else:
                        st.success(f"📝 Ghi chú: Máy {target_code} vẫn ổn định. Ưu tiên bảo trì.")
                    st.dataframe(res[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']], use_container_width=True)
                else:
                    st.warning(f"❌ Không tìm thấy mã máy '{target_code}' trong cơ sở dữ liệu. Sếp hãy kiểm tra lại số máy.")
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("📋 Hệ Thống Ưu Tiên Mua Sắm")
    if not df_filtered.empty:
        df_p = df_filtered.copy()
        df_p['ƯU TIÊN'] = df_p.apply(lambda r: "🔴 KHẨN CẤP" if any(x in str(r['LÝ_DO_HỎNG']) for x in ['Màn', 'Main']) else "🟢 BÌNH THƯỜNG", axis=1)
        st.dataframe(df_p[['ƯU TIÊN', 'MÃ_MÁY', 'LÝ_DO_HỎNG', 'NGAY_FIX', 'VÙNG_MIỀN']], use_container_width=True)

with tab3:
    st.markdown("""
    <div class="guide-box">
        <h3>📖 QUY TRÌNH VẬN HÀNH 2026</h3>
        <p><b>Bước 1:</b> Kiểm tra 3 thẻ KPI đầu trang để nắm tổng thể chi phí rủi ro.</p>
        <p><b>Bước 2:</b> Sử dụng <b>Trợ lý AI</b> để kiểm tra tiền sử của máy trước khi duyệt linh kiện thay thế.</p>
        <p><b>Bước 3:</b> Tải báo cáo CSV ở sidebar hàng tuần để lưu trữ dữ liệu đối soát.</p>
        <p><b>Bước 4:</b> Các máy có trạng thái "Nguy kịch" cần được lập danh sách thanh lý định kỳ.</p>
    </div>
    """, unsafe_allow_html=True)
