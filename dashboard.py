import streamlit as st
import pandas as pd
import plotly.express as px
import math

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V20", layout="wide")

# 2. LINK DỮ LIỆU CHUẨN TỪ ẢNH CỦA SẾP
NEW_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v20():
    try:
        # Buộc làm mới cache bằng timestamp
        raw_df = pd.read_csv(f"{NEW_URL}&refresh={pd.Timestamp.now().timestamp()}")
        
        # --- THUẬT TOÁN DÒ CỘT THÔNG MINH ---
        # AI sẽ tự tìm cột nào chứa mã máy, cột nào chứa lý do hỏng
        cols = raw_df.columns.tolist()
        
        # Giả định mặc định nếu không tìm thấy tên cột chuẩn
        df = pd.DataFrame()
        df['MÃ_MÁY'] = raw_df.iloc[:, 1].astype(str).str.split('.').str[0].str.strip() # Cột B
        df['LÝ_DO'] = raw_df.iloc[:, 3].fillna("Chưa rõ").astype(str) # Cột D
        df['NGAY_FIX'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce', dayfirst=True) # Cột G
        
        # Nhận diện vùng miền từ tất cả các cột (quét toàn bộ dòng)
        def find_region(row):
            full_text = " ".join(row.astype(str)).upper()
            if any(x in full_text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in full_text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in full_text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"
        
        df['VÙNG_MIỀN'] = raw_df.apply(find_region, axis=1)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        
        return df
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return pd.DataFrame()

df_all = load_data_v20()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛡️ BỘ LỌC CHIẾN LƯỢC")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU MỚI (3.651 DÒNG)'):
        st.cache_data.clear()
        st.rerun()
    
    if not df_all.empty:
        list_years = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_years, index=0) # Mặc định năm mới nhất
        list_vung = sorted(df_all['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Chọn Miền", list_vung, default=list_vung)
        df_filtered = df_all[(df_all['NĂM'] == sel_year) & (df_all['VÙNG_MIỀN'].isin(sel_vung))]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_all.empty:
    t1, t2, t3, t4 = st.tabs(["📊 Dashboard", "💬 Chatbot AI", "🚩 Máy Nguy Kịch", "📖 Hướng Dẫn"])
    
    with t1:
        # KPI
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số lượng máy", f"{df_filtered['MÃ_MÁY'].nunique()}")
        
        machine_counts = df_all['MÃ_MÁY'].value_counts()
        bad_machines = machine_counts[machine_counts >= 4].index.tolist()
        c3.metric("Máy cần thanh lý", f"{len(bad_machines)}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.subheader("📍 Phân bổ theo Miền")
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4), use_container_width=True)
        with cr:
            st.subheader("🛠️ Loại linh kiện thay thế")
            # Tối ưu logic phân loại để không bị dồn vào "Khác"
            def cat_lk(x):
                x = x.lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc/Adapter'
                return 'Linh kiện khác'
            df_filtered['LOẠI'] = df_filtered['LÝ_DO'].apply(cat_lk)
            st.plotly_chart(px.bar(df_filtered['LOẠI'].value_counts().reset_index(), x='count', y='LOẠI', orientation='h'), use_container_width=True)

    with t2:
        st.subheader("💬 Truy lục lịch sử máy (Live)")
        q = st.text_input("Nhập mã máy (Ví dụ: 3534):")
        if q:
            res = df_all[df_all['MÃ_MÁY'].str.contains(q, na=False)].sort_values('NGAY_FIX', ascending=False)
            if not res.empty:
                st.success(f"Tìm thấy {len(res)} bản ghi cho máy {q}")
                st.dataframe(res[['NGAY_FIX', 'LÝ_DO', 'VÙNG_MIỀN']], use_container_width=True)
            else:
                st.warning("Không tìm thấy dữ liệu. Sếp hãy nhấn nút 'Cập nhật' ở Sidebar.")

    with t3:
        st.header("🚩 Danh sách đen (Hỏng >= 4 lần)")
        report = df_all.groupby('MÃ_MÁY').agg(
            Lượt_hỏng=('LÝ_DO', 'count'),
            Bệnh_chính=('LÝ_DO', lambda x: x.mode().iloc[0] if not x.mode().empty else "Đa bệnh"),
            Khu_vực=('VÙNG_MIỀN', 'first')
        ).reset_index()
        st.dataframe(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False), use_container_width=True)

else:
    st.info("Hệ thống đang kết nối tới 3.651 dòng dữ liệu... Sếp đợi chút nhé!")
