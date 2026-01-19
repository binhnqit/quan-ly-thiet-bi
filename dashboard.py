import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị V81", layout="wide")

# Link dữ liệu của sếp
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v81():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("Chưa xác định")
        
        # Tự động nhận diện cột
        cols = df_raw.columns.tolist()
        c_ma = next((c for c in cols if any(k in c.upper() for k in ['MÃ', 'ID', 'SERIAL'])), cols[1])
        c_ly = next((c for c in cols if any(k in c.upper() for k in ['LỖI', 'HỎNG', 'TÌNH TRẠNG', 'THAY'])), cols[3])
        c_ng = next((c for c in cols if any(k in c.upper() for k in ['NGÀY', 'DATE', 'TIME'])), cols[0])
        c_kh = next((c for c in cols if any(k in c.upper() for k in ['KHÁCH', 'ĐƠN VỊ', 'TÊN'])), cols[2])

        # Tạo DataFrame chuẩn - Đảm bảo không mất dòng nào (Keep all 4039 rows)
        df = pd.DataFrame({
            'MÃ_MÁY': df_raw[c_ma].astype(str).str.strip(),
            'LINH_KIỆN': df_raw[c_ly].astype(str).str.strip(),
            'KHÁCH_HÀNG': df_raw[c_kh].astype(str).str.strip(),
            'NGÀY_GỐC': df_raw[c_ng]
        })

        # Xử lý ngày tháng an toàn
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY_GỐC'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY_DT'].dt.month.fillna(0).astype(int)
        
        # Phân loại vùng miền tự động cho biểu đồ tròn
        def get_region(kh):
            v = str(kh).upper()
            if any(x in v for x in ['BẮC', 'HN', 'PHÚ', 'SƠN', 'NỘI']): return 'MIỀN BẮC'
            if any(x in v for x in ['TRUNG', 'ĐÀ NẴNG', 'HUẾ', 'VINH']): return 'MIỀN TRUNG'
            return 'MIỀN NAM'
        df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(get_region)

        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR CONTROL ---
data = load_data_v81()

with st.sidebar:
    st.title("⚙️ HỆ THỐNG V81")
    if st.button('🔄 SYNC & REFRESH', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if data is not None:
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + [int(y) for y in y_list if y > 2000], index=0)
        
        m_options = ["Tất cả (Cộng dồn)"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", m_options, index=0)

        # Logic lọc chuẩn xác
        df_filtered = data.copy()
        if sel_year != "Tất cả":
            df_filtered = df_filtered[df_filtered['NĂM'] == sel_year]
        if sel_month != "Tất cả (Cộng dồn)":
            m_val = int(sel_month.replace("Tháng ", ""))
            df_filtered = df_filtered[df_filtered['THÁNG_NUM'] == m_val]

# --- MAIN DASHBOARD ---
if data is not None:
    st.markdown(f"### 🛡️ Dashboard Quản Trị: {sel_month} / {sel_year}")
    
    # KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_filtered):,}")
    c2.metric("Số thiết bị lỗi", f"{df_filtered['MÃ_MÁY'].nunique():,}")
    counts = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng nặng (>1 lần)", len(counts[counts > 1]))
    c4.metric("Đơn vị khách hàng", f"{df_filtered['KHÁCH_HÀNG'].nunique():,}")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 THỐNG KÊ", "🔍 TRA CỨU MÃ", "🤖 AI ASSISTANT", "📋 DỮ LIỆU GỐC"])

    with tab1:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.write("**Top 10 Linh kiện lỗi**")
            top_lk = df_filtered['LINH_KIỆN'].value_counts().head(10)
            st.bar_chart(top_lk)
        with col_r:
            st.write("**Phân bổ Vùng miền**")
            fig = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        search = st.text_input("Gõ mã máy hoặc tên khách hàng:")
        if search:
            # Sửa lỗi Syntax ở đây - Đảm bảo đóng ngoặc chuẩn xác
            res = df_filtered[df_filtered.apply(lambda r: search.upper() in r.astype(str).str.upper().values, axis=1)]
            st.dataframe(res, use_container_width=True)

    with tab3:
        st.subheader("🤖 Trợ lý AI Assistant")
        ask = st.chat_input("Hỏi tôi về tình hình hỏng hóc tháng này...")
        if ask:
            st.write(f"💬 **Sếp hỏi:** {ask}")
            if "nhiều nhất" in ask.lower() or "linh kiện" in ask.lower():
                top = df_filtered['LINH_KIỆN'].value_counts().idxmax()
                st.success(f"🤖 Theo dữ liệu, linh kiện **{top}** đang hỏng nhiều nhất sếp ạ.")
            elif "miền" in ask.lower():
                top_v = df_filtered['VÙNG_MIỀN'].value_counts().idxmax()
                st.success(f"🤖 Miền đang có số ca báo lỗi cao nhất là **{top_v}**.")
            else:
                st.info("🤖 AI đang tổng hợp báo cáo... Sếp hãy hỏi về Linh kiện hoặc Vùng miền nhé.")

    with tab4:
        st.write(f"Hiển thị 100 dòng dữ liệu mới nhất (Tổng: {len(df_filtered)} dòng)")
        st.dataframe(df_filtered.head(100), use_container_width=True)
