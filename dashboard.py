import streamlit as st
import pandas as pd
import plotly.express as px
import math
import base64

# Cấu hình giao diện Pro
st.set_page_config(page_title="Quản Trị Tài Sản AI", layout="wide")

# CSS để làm đẹp giao diện
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .guide-box { background-color: #f0f7ff; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A; }
    h1 { color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# 1. KẾT NỐI DỮ LIỆU
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_pro():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
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
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_pro()

# --- SIDEBAR: BỘ LỌC CHIẾN LƯỢC ---
with st.sidebar:
    st.title("🛡️ BỘ LỌC AI")
    
    # Lọc Năm
    list_years = sorted(df['NĂM'].unique(), reverse=True)
    sel_year = st.selectbox("📅 Chọn Năm", list_years)
    
    # Lọc Miền (Mới bổ sung theo yêu cầu Pro)
    list_vung = sorted(df['VÙNG_MIỀN'].unique())
    sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
    
    # Lọc Tháng
    df_temp = df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))]
    list_months = sorted(df_temp['THÁNG'].unique())
    sel_months = st.multiselect("📆 Chọn Tháng", list_months, default=list_months)
    
    st.divider()
    if st.button("📄 Chuẩn bị Báo cáo"):
        st.toast("Dữ liệu đã sẵn sàng để trích xuất!")

# Lọc dữ liệu tổng
df_filtered = df[(df['NĂM'] == sel_year) & 
                 (df['THÁNG'].isin(sel_months)) & 
                 (df['VÙNG_MIỀN'].isin(sel_vung))]

# --- GIAO DIỆN TABS ---
tab1, tab2 = st.tabs(["📊 Báo Cáo Chiến Lược", "📖 Hướng Dẫn Vận Hành"])

with tab1:
    st.title("🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI")
    
    # KPI ROWS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    
    # Dự báo ngân sách đơn giản
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    n_m = len(sel_months) if sel_months else 1
    est_budget = sum([math.ceil((v/n_m)*1.2)*500000 for v in forecast_counts.values])
    
    c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    c3.metric("Số máy đỏ (Nguy kịch)", f"{(df['MÃ_MÁY'].value_counts() >= 4).sum()}")
    c4.metric("Khu vực đang xem", f"{len(sel_vung)} Miền")

    st.divider()

    # CHATBOT AI TRUY LỤC (KHÔNG BỊ LỌC)
    st.subheader("💬 Trợ lý Tra cứu Hồ sơ toàn hệ thống")
    user_msg = st.text_input("Gõ mã máy để xem lịch sử sửa chữa:", placeholder="Ví dụ: 3534")
    if user_msg:
        import re
        m = re.search(r'\d+', user_msg)
        if m:
            code = m.group()
            h = df[df['MÃ_MÁY'] == code].sort_values('NGAY_FIX', ascending=False)
            if not h.empty:
                st.info(f"🔍 Tìm thấy {len(h)} lần sửa cho máy {code}:")
                for _, r in h.iterrows():
                    st.write(f"- **{r['NGAY_FIX'].strftime('%d/%m/%Y')}**: {r['LÝ_DO_HỎNG']} ({r['VÙNG_MIỀN']})")
            else: st.warning("Không tìm thấy dữ liệu.")

    st.divider()

    # BIỂU ĐỒ PHÂN TÍCH
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ hỏng theo Vùng")
        st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5), use_container_width=True)
    with col_r:
        st.subheader("🛠️ Top 10 linh kiện/Lý do")
        st.plotly_chart(px.bar(df_filtered['LÝ_DO_HỎNG'].value_counts().head(10), orientation='h'), use_container_width=True)

    # DANH SÁCH SỨC KHỎE
    st.subheader("🌡️ Chỉ số sức khỏe thiết bị")
    health = df['MÃ_MÁY'].value_counts().reset_index()
    health.columns = ['Mã Máy', 'Lượt hỏng']
    health['Trạng thái'] = health['Lượt hỏng'].apply(lambda x: "🔴 Nguy kịch" if x>=4 else ("🟠 Yếu" if x==3 else "🟢 Tốt"))
    st.dataframe(health.head(15), use_container_width=True)

with tab2:
    st.markdown("""
    <div class="guide-box">
        <h3>📖 HƯỚNG DẪN SỬ DỤNG CHO NHÂN VIÊN</h3>
        <p>Để AI học chính xác nhất, sếp hãy yêu cầu kỹ thuật viên tuân thủ:</p>
        <ul>
            <li><b>Bước 1:</b> Nhập liệu vào Google Sheets đúng cột mã máy (Chỉ nhập số).</li>
            <li><b>Bước 2:</b> Sử dụng bộ lọc Miền ở bên trái để xem báo cáo riêng từng kho/văn phòng.</li>
            <li><b>Bước 3:</b> Tra cứu lịch sử máy bằng Chatbot trước khi quyết định thay linh kiện.</li>
            <li><b>Bước 4:</b> Nếu máy hiện trạng thái <b>Nguy kịch</b>, lập biên bản thanh lý.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
