import streamlit as st
import pandas as pd
import plotly.express as px
import math

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V19", layout="wide")

# 2. KẾT NỐI DỮ LIỆU MỚI (ĐÃ CẬP NHẬT THEO ẢNH CỦA SẾP)
NEW_PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5) # Ép làm mới mỗi 5 giây
def load_data_v19():
    try:
        # Thêm biến timestamp để buộc Google Sheets trả về bản mới nhất
        df = pd.read_csv(f"{NEW_PUBLISHED_URL}&cache_bust={pd.Timestamp.now().timestamp()}")
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # Chuẩn hóa mã máy
        def clean_code(val):
            if pd.isna(val): return ""
            return str(val).split('.')[0].strip()
        df['MÃ_MÁY'] = df['COL_1'].apply(clean_code)
        
        # Nhận diện vùng miền từ nội dung
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"
        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        
        # Xử lý thời gian và lý do hỏng
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ").astype(str).str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df_all = load_data_v19()

# --- SIDEBAR & BỘ LỌC ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if st.button('🔄 ÉP LÀM MỚI DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        # Mặc định chọn năm 2026 theo yêu cầu
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=list_years.index(2026) if 2026 in list_years else 0)
        
        list_vung = sorted(df_all['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        
        df_filtered = df_all[(df_all['NĂM'] == sel_year) & (df_all['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI</h1>', unsafe_allow_html=True)

if not df_all.empty:
    tab1, tab2, tab4, tab3 = st.tabs(["📊 Tổng Quan & AI Chat", "⚡ Ưu Tiên Mua Sắm", "🚩 Danh Sách Nguy Kịch", "📖 Hướng Dẫn"])

    with tab1:
        # THẺ KPI
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng lượt hỏng (Lọc)", f"{len(df_filtered)} ca")
        
        # Tính toán ngân sách dự phòng
        est_budget = len(df_filtered) * 750000 # Ước tính trung bình 750k/ca
        c2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
        
        # Thống kê máy nguy kịch (hỏng >= 4 lần)
        machine_counts = df_all['MÃ_MÁY'].value_counts()
        crit_list = machine_counts[machine_counts >= 4].index.tolist()
        curr_crit = df_filtered[df_filtered['MÃ_MÁY'].isin(crit_list)]['MÃ_MÁY'].nunique()
        c3.metric("Máy Nguy kịch (Đỏ)", f"{curr_crit}")

        st.divider()
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📍 Tỷ lệ hỏng theo Vùng miền")
            fig_pie = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_r:
            st.subheader("🛠️ Thống kê linh kiện")
            df_filtered['LK'] = df_filtered['LÝ_DO_HỎNG'].apply(lambda x: 'Pin' if 'pin' in x.lower() else ('Màn hình' if 'màn' in x.lower() else 'Khác'))
            fig_bar = px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', color='LK')
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        # CHATBOT TRUY VẤN
        st.subheader("💬 Trợ lý AI (Quét 3.651 dòng dữ liệu)")
        q = st.text_input("Gõ mã máy (VD: 3534):")
        if q:
            import re
            m = re.search(r'\d+', q)
            if m:
                code = m.group()
                history = df_all[df_all['MÃ_MÁY'] == code].sort_values('NGAY_FIX', ascending=False)
                if not history.empty:
                    st.success(f"Dữ liệu: Máy {code} đã hỏng {len(history)} lần.")
                    st.dataframe(history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']], use_container_width=True)
                else:
                    st.warning(f"Không tìm thấy mã máy {code} trong toàn bộ 3.651 dòng.")

    with tab4:
        st.header("🚩 Danh Sách Máy Hỏng Nhiều (>= 4 lần)")
        report = df_all.groupby('MÃ_MÁY').agg(
            So_Lan_Hong=('LÝ_DO_HỎNG', 'count'),
            Loi_Pho_Bien=('LÝ_DO_HỎNG', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa lỗi"),
            Vung_Mien=('VÙNG_MIỀN', 'first')
        ).reset_index()
        st.dataframe(report[report['So_Lan_Hong'] >= 4].sort_values('So_Lan_Hong', ascending=False), use_container_width=True, hide_index=True)
else:
    st.warning("Đang tải dữ liệu từ Google Sheets... Sếp vui lòng đợi 5-10 giây.")
