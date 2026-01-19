import streamlit as st
import pandas as pd
import plotly.express as px
import math

# 1. CẤU HÌNH & LÀM SẠCH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - Live", layout="wide")

# Nút bấm làm mới dữ liệu thủ công nếu sếp cần gấp
if st.sidebar.button('🔄 Cập nhật dữ liệu mới từ Sheets'):
    st.cache_data.clear()
    st.rerun()

# 2. KẾT NỐI DỮ LIỆU "SỐNG"
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=10) # Giảm thời gian chờ xuống 10 giây để dữ liệu nhạy hơn
def load_live_data():
    try:
        # Ép pandas đọc mới hoàn toàn bằng cách thêm tham số thời gian ẩn
        df = pd.read_csv(f"{PUBLISHED_URL}&timestamp={pd.Timestamp.now().timestamp()}")
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
    except Exception as e:
        st.error(f"Lỗi kết nối Sheets: {e}")
        return pd.DataFrame()

df_all = load_live_data()

# 3. BỘ LỌC CHIẾN LƯỢC (MẶC ĐỊNH 2026)
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=list_years.index(2026) if 2026 in list_years else 0)
        
        list_vung = sorted(df_all['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        
        df_filtered = df_all[(df_all['NĂM'] == sel_year) & (df_all['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# 4. CHẨN ĐOÁN BỆNH NỀN (Quét toàn bộ file)
if not df_all.empty:
    machine_report = df_all.groupby('MÃ_MÁY').agg(
        So_Lan_Hong=('LÝ_DO_HỎNG', 'count'),
        Loi_Pho_Bien=('LÝ_DO_HỎNG', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa lỗi")
    ).reset_index()
    critical_data = machine_report[machine_report['So_Lan_Hong'] >= 4].sort_values('So_Lan_Hong', ascending=False)
else:
    critical_data = pd.DataFrame()

# 5. GIAO DIỆN CHÍNH
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

tab1, tab2, tab4, tab3 = st.tabs(["📊 Tổng Quan & AI Chat", "⚡ Ưu Tiên Mua Sắm", "🚩 Danh Sách Nguy Kịch", "📖 Hướng Dẫn"])

with tab1:
    # KPI CARDS
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng (Lọc)", f"{len(df_filtered)} ca")
    
    # Tính ngân sách dự phòng thông minh hơn
    if not df_filtered.empty:
        top_err = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5).sum()
        est_budget = top_err * 650000 # Ước tính 650k/ca cho linh kiện top
        c2.metric("Dự toán sửa chữa", f"{est_budget:,.0f}đ")
    
    c3.metric("Máy Nguy kịch (Toàn file)", f"{len(critical_data)}")

    st.divider()
    
    # BIỂU ĐỒ CHUẨN (Fix hiển thị bị lệch)
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ hỏng theo Miền")
        fig_pie = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_r:
        st.subheader("🛠️ Top Linh Kiện Hỏng")
        df_filtered['LK'] = df_filtered['LÝ_DO_HỎNG'].apply(lambda x: 'Pin' if 'pin' in x.lower() else ('Màn hình' if 'màn' in x.lower() else 'Khác'))
        fig_bar = px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK')
        fig_bar.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    # CHATBOT TRUY VẤN REAL-TIME
    st.subheader("💬 Trợ lý AI (Truy vấn trực tiếp Sheets)")
    q = st.text_input("Gõ mã máy để kiểm tra dữ liệu mới nhất:")
    if q:
        import re
        m = re.search(r'\d+', q)
        if m:
            code = m.group()
            # Quét trực tiếp trên df_all vừa load từ Sheets
            history = df_all[df_all['MÃ_MÁY'] == code].sort_values('NGAY_FIX', ascending=False)
            if not history.empty:
                st.success(f"Dữ liệu mới nhất: Máy {code} đã hỏng {len(history)} lần.")
                st.table(history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
            else:
                st.warning(f"Không tìm thấy máy {code}. Sếp hãy kiểm tra lại file Sheets.")

with tab4:
    st.header("🚩 Phân Tích Máy Hỏng Hệ Thống")
    st.dataframe(critical_data, use_container_width=True, hide_index=True)

with tab2:
    # Giữ nguyên logic mua sắm khẩn cấp
    df_p = df_filtered.copy()
    if not df_p.empty:
        df_p['ƯU TIÊN'] = df_p.apply(lambda r: "🔴 GẤP" if any(x in str(r['LÝ_DO_HỎNG']) for x in ['Màn', 'Main']) else "🟢 THƯỜNG", axis=1)
        st.dataframe(df_p[['ƯU TIÊN', 'MÃ_MÁY', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']], use_container_width=True)
