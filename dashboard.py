import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN (Bản Pro)
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản V75", layout="wide")

# CSS để làm đẹp các thành phần giao diện
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #e1e4e8; border-radius: 5px 5px 0 0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v75():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # Dò cột tự động
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(50)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['MÃ', '3534', '1102']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA']) or df_raw.columns[3]
        c_ng = find_col(['/', '202', 'NGÀY']) or df_raw.columns[0]
        c_kh = find_col(['QUANG TRUNG', 'SƠN HẢI', 'KHÁCH']) or df_raw.columns[2]

        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LINH_KIỆN_HƯ'] = df_raw[c_ly].astype(str).str.strip()
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # Xử lý ngày tháng chuyên sâu
        df['NGÀY_DT'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY_DT'].dt.month.fillna(1).astype(int)
        
        # Phân loại vùng miền (Tự động dựa trên từ khóa khách hàng)
        def set_region(kh):
            v = str(kh).upper()
            if any(x in v for x in ['BẮC', 'HN', 'PHÚ', 'SƠN LÀ']): return 'MIỀN BẮC'
            if any(x in v for x in ['TRUNG', 'ĐÀ NẴNG', 'HUẾ', 'VINH']): return 'MIỀN TRUNG'
            return 'MIỀN NAM'
        df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(set_region)
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR: GIAO DIỆN LỌC CHUYÊN NGHIỆP ---
with st.sidebar:
    st.markdown("### ⚙️ HỆ THỐNG ĐIỀU KHIỂN")
    if st.button('🚀 CẬP NHẬT DỮ LIỆU TỨC THÌ', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    data = load_data_v75()
    
    if data is not None:
        # Chọn Năm
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", y_list, index=0)
        
        # Chọn Tháng (Tích hợp "Tất cả" để bỏ chế độ Radio amatuer)
        m_options = ["Tất cả (Cộng dồn)"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng báo cáo", m_options, index=0)
        
        # Logic lọc dữ liệu ngầm
        if sel_month == "Tất cả (Cộng dồn)":
            df_final = data[data['NĂM'] == sel_year]
            filter_desc = f"Cộng dồn cả năm {sel_year}"
        else:
            m_num = int(sel_month.replace("Tháng ", ""))
            df_final = data[(data['NĂM'] == sel_year) & (data['THÁNG_NUM'] == m_num)]
            filter_desc = f"Chi tiết {sel_month} / {sel_year}"
            
        st.success(f"📊 Dòng dữ liệu: {len(df_final):,}")
    else:
        df_final = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown(f'<h1 style="text-align:center; color:#1E3A8A;">🛡️ DASHBOARD QUẢN TRỊ LIVE DATA</h1>', unsafe_allow_html=True)
st.markdown(f'<p style="text-align:center; color:#666;">Chế độ: <b>{filter_desc}</b></p>', unsafe_allow_html=True)

if not df_final.empty:
    # 1. KPI Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Tổng ca hỏng", f"{len(df_final):,}")
    with m2: st.metric("Số thiết bị lỗi", f"{df_final['MÃ_MÁY'].nunique():,}")
    with m3: 
        counts = df_final['MÃ_MÁY'].value_counts()
        st.metric("Máy hỏng nặng (>2 lần)", len(counts[counts > 2]))
    with m4: st.metric("Đơn vị yêu cầu", df_final['KHÁCH_HÀNG'].nunique())

    # 2. Tabs
    t1, t2, t3, t4, t5 = st.tabs(["📊 BÁO CÁO", "🔍 TRA CỨU", "🚩 DANH SÁCH ĐEN", "🤖 AI ASSISTANT", "📖 HƯỚNG DẪN"])

    with t1:
        st.subheader("🛠️ Phân tích lỗi & Vùng miền")
        col_bar, col_pie = st.columns([2, 1])
        with col_bar:
            top_lk = df_final[df_final['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
            fig_bar = px.bar(top_lk, orientation='h', labels={'value':'Số ca', 'index':'Linh kiện'}, color=top_lk.index)
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_pie:
            fig_pie = px.pie(df_final, names='VÙNG_MIỀN', hole=0.5, 
                             color_discrete_map={'MIỀN BẮC':'#EF553B', 'MIỀN TRUNG':'#FECB52', 'MIỀN NAM':'#636EFA'})
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        search = st.text_input("Tra cứu nhanh Mã máy hoặc Tên khách hàng:")
        if search:
            res = df_final[df_final.apply(lambda row: search.upper() in row.astype(str).str.upper().values, axis=1)]
            st.dataframe(res, use_container_width=True)

    with t3:
        st.subheader("🚩 Danh sách máy hỏng tái diễn (Cảnh báo thay thế)")
        st.dataframe(counts[counts > 2].reset_index().rename(columns={'count':'Số lần lỗi'}), use_container_width=True)

    with t4:
        st.subheader("🤖 Trợ lý AI Assistant (Live Data)")
        ask = st.chat_input("Hỏi tôi về dữ liệu tháng này...")
        if ask:
            st.write(f"💬 **Sếp hỏi:** {ask}")
            if "đơn vị" in ask.lower() or "khách hàng" in ask.lower():
                top = df_final['KHÁCH_HÀNG'].value_counts().idxmax()
                st.info(f"🤖 **AI trả lời:** Đơn vị **{top}** đang dẫn đầu về số ca lỗi.")
            elif "linh kiện" in ask.lower():
                top_lk = df_final['LINH_KIỆN_HƯ'].value_counts().idxmax()
                st.info(f"🤖 **AI trả lời:** Linh kiện **{top_lk}** là nhóm hỏng nhiều nhất.")
            else:
                st.info("🤖 AI đang phân tích sâu dữ liệu, sếp hãy hỏi về Linh kiện hoặc Đơn vị lỗi nhé!")

    with t5:
        st.markdown("### 📖 Hướng dẫn V75 PRO\n- Chế độ lọc được tích hợp trực tiếp vào mục Chọn Tháng.\n- Biểu đồ vùng miền tự động phân loại theo danh sách khách hàng.")

else:
    st.warning("⚠️ Không tìm thấy dữ liệu cho lựa chọn này. Sếp hãy nhấn Cập Nhật hoặc chọn thời gian khác.")
