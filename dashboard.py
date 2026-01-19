import streamlit as st
import pandas as pd
import plotly.express as px
import math

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V21", layout="wide")

# 2. LINK DỮ LIỆU ĐÃ XÁC THỰC TỪ ẢNH CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_final():
    try:
        # Đọc dữ liệu thô và ép kiểu chuỗi để tránh lỗi định dạng
        raw_df = pd.read_csv(f"{DATA_URL}&cache={pd.Timestamp.now().timestamp()}", dtype=str)
        
        # Tạo DataFrame sạch với các cột cố định
        df = pd.DataFrame()
        
        # Ép tọa độ cột chính xác theo cấu trúc Google Sheets của sếp
        df['MÃ_MÁY'] = raw_df.iloc[:, 1].str.split('.').str[0].str.strip() # Cột B
        df['LÝ_DO'] = raw_df.iloc[:, 3].fillna("Không xác định") # Cột D
        df['NGAY_FIX'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce', dayfirst=True) # Cột G
        
        # Nhận diện vùng miền linh hoạt
        def detect(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = raw_df.apply(detect, axis=1)
        
        # Lọc bỏ dòng trống và phân loại thời gian
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame()

df_all = load_data_final()

# --- SIDEBAR QUẢN TRỊ ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU (3.651 DÒNG)'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0)
        
        list_vung = sorted(df_all['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        
        df_filtered = df_all[(df_all['NĂM'] == sel_year) & (df_all['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    tab1, tab2, tab4, tab3 = st.tabs(["📊 Dashboard", "💬 Chatbot AI", "🚩 Máy Nguy Kịch", "📖 Hướng Dẫn"])

    with tab1:
        # KPI CHUẨN
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số lượng máy", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        # Tính toán máy nguy kịch toàn hệ thống
        bad_machines = df_all['MÃ_MÁY'].value_counts()
        crit_count = len(bad_machines[bad_machines >= 4])
        c3.metric("Tổng máy cần thanh lý", f"{crit_count}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Phân bổ theo Miền")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold), use_container_width=True)
        
        with cr:
            st.subheader("🛠️ Thống kê linh kiện")
            # Hàm phân loại linh kiện để sửa lỗi bị dồn vào "Khác"
            def classify_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'main' in x: return 'Mainboard'
                if 'ổ' in x or 'ssd' in x: return 'Ổ cứng'
                return 'Linh kiện khác'
            
            df_filtered['LINH_KIỆN'] = df_filtered['LÝ_DO'].apply(classify_lk)
            fig_bar = px.bar(df_filtered['LINH_KIỆN'].value_counts().reset_index(), 
                             x='count', y='LINH_KIỆN', orientation='h', 
                             color='LINH_KIỆN', color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("💬 Tra cứu hồ sơ máy (Live)")
        q = st.text_input("Nhập mã máy để AI quét 3.651 dòng:")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False, case=False)].sort_values('NGAY_FIX', ascending=False)
            if not res.empty:
                st.success(f"Tìm thấy {len(res)} lần bảo trì cho máy {q}")
                st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']], use_container_width=True)
            else:
                st.warning("Mã máy không tồn tại hoặc dữ liệu chưa được tải lên.")

    with tab4:
        st.header("🚩 Danh sách thiết bị hỏng hệ thống")
        report = df_all.groupby('MÃ_MÁY').agg(
            Số_lần_hỏng=('LÝ_DO', 'count'),
            Lỗi_hay_gặp=('LÝ_DO', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa lỗi"),
            Vùng_miền=('VÙNG_MIỀN', 'first')
        ).reset_index()
        st.dataframe(report[report['Số_lần_hỏng'] >= 4].sort_values('Số_lần_hỏng', ascending=False), use_container_width=True, hide_index=True)

else:
    st.warning("Hệ thống đang đồng bộ dữ liệu... Sếp vui lòng nhấn 'Cập nhật' ở sidebar nếu đợi quá 10 giây.")
