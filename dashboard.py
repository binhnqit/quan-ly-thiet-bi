import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KHỞI TẠO GIAO DIỆN VIỆT HÓA
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

# CSS tạo phong cách Enterprise
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stMetric { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1 { color: #1E3A8A; font-family: 'Arial'; }
    </style>
    """, unsafe_allow_html=True)

# 2. TẢI DỮ LIỆU (Quét toàn bộ 3.976 dòng)
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(PUBLISHED_URL)
    df.columns = [f"COL_{i}" for i in range(len(df.columns))]
    df['VÙNG_MIỀN'] = df.apply(lambda r: "Miền Bắc" if "Bắc" in str(r.values) else ("Miền Nam" if "Nam" in str(r.values) else "Miền Trung"), axis=1)
    df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0].str.strip()
    df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ")
    df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
    df['NĂM'] = df['NGAY_FIX'].dt.year
    df['THÁNG'] = df['NGAY_FIX'].dt.month
    return df.dropna(subset=['NGAY_FIX'])

df = load_data()

# --- BỘ LỌC CHIẾN LƯỢC ---
with st.sidebar:
    st.title("🛡️ BỘ LỌC CHUYÊN GIA")
    sel_year = st.selectbox("Năm", sorted(df['NĂM'].unique(), reverse=True), index=0)
    
    # BỔ SUNG BỘ LỌC MIỀN THEO YÊU CẦU
    sel_vung = st.multiselect("Khu vực", ["Miền Bắc", "Miền Trung", "Miền Nam"], default=["Miền Bắc", "Miền Trung", "Miền Nam"])
    
    list_months = sorted(df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))]['THÁNG'].unique())
    sel_months = st.multiselect("Tháng", list_months, default=list_months)

df_filtered = df[(df['NĂM'] == sel_year) & (df['THÁNG'].isin(sel_months)) & (df['VÙNG_MIỀF'].isin(sel_vung))]

# --- GIAO DIỆN CHÍNH ---
tab_dashboard, tab_huongdan = st.tabs(["📊 BÁO CÁO TỔNG QUAN", "📖 HƯỚNG DẪN SỬ DỤNG"])

with tab_dashboard:
    st.header("🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI")
    
    # KPI chính
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt hỏng", f"{len(df_filtered)} ca")
    c2.metric("Số máy phát sinh lỗi", f"{df_filtered['MÃ_MÁY'].nunique()} máy")
    c3.metric("Máy cần thanh lý (Lỗi >= 4)", f"{(df['MÃ_MÁY'].value_counts() >= 4).sum()}")

    st.divider()

    # TRỢ LÝ AI (Sửa lỗi không tìm thấy mã máy)
    st.subheader("💬 Trợ lý ảo Tra cứu Hồ sơ (Toàn hệ thống)")
    ma_tra_cuu = st.text_input("Gõ mã máy (VD: 5281):", key="search_ai")
    if ma_tra_cuu:
        # AI quét trên toàn bộ data gốc, không bị chặn bởi bộ lọc miền/tháng
        ket_qua = df[df['MÃ_MÁY'] == ma_tra_cuu].sort_values('NGAY_FIX', ascending=False)
        if not ket_qua.empty:
            st.success(f"Tìm thấy {len(ket_qua)} lần hỏng cho máy {ma_tra_cuu}:")
            st.table(ket_qua[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
        else:
            st.error(f"Máy {ma_tra_cuu} không có trong 3.976 dòng dữ liệu. Sếp kiểm tra lại file gốc nhé!")

    # BIỂU ĐỒ
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ lỗi theo khu vực")
        st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5), use_container_width=True)
    with col_r:
        st.subheader("🛠️ Top 15 Lý do hỏng")
        st.plotly_chart(px.bar(df_filtered['LÝ_DO_HỎNG'].value_counts().head(15), orientation='h'), use_container_width=True)

with tab_huongdan:
    st.info("### 📘 Hướng dẫn vận hành cho Kỹ thuật viên")
    st.write("""
    1. **Nhập liệu:** Nhập mã máy vào cột A, ngày vào cột F trên Google Sheets. 
    2. **Định dạng:** Chỉ nhập số máy (VD: 3534), không nhập chữ để AI dễ tra cứu.
    3. **Tra cứu:** Sử dụng ô 'Trợ lý ảo' để xem lịch sử máy trước khi quyết định thay linh kiện đắt tiền.
    4. **Thanh lý:** Nếu máy hiện cảnh báo 'Đỏ' hoặc hỏng trên 4 lần, cần lập biên bản thanh lý sớm.
    """)
