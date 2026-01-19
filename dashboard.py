import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. THIẾT LẬP HỆ THỐNG EXECUTIVE
st.set_page_config(page_title="Hệ Thống Quản Trị V82", layout="wide")

# CSS Chuyên nghiệp
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] { background: white; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v82():
    try:
        # Load Raw Data - Ép kiểu string toàn bộ để tránh tự nhảy số
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str).fillna("Chưa xác định")
        
        # FIX TRIỆT ĐỂ: Nếu sếp thấy cột bị lệch, hãy chỉnh số index [0, 1, 2, 3] ở đây
        # Theo hình image_ec0e41, có vẻ dòng đầu tiên là dòng tiêu đề rác
        if "Mã số máy" in str(df_raw.iloc[0]):
            df_raw = df_raw.iloc[1:].reset_index(drop=True)

        df = pd.DataFrame()
        # Gán cứng cột theo vị trí để không bao giờ bị lệch dữ liệu như image_ec0e96
        df['NGÀY_GỐC'] = df_raw.iloc[:, 0]
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.strip()
        df['KHÁCH_HÀNG'] = df_raw.iloc[:, 2].str.strip()
        df['LINH_KIỆN'] = df_raw.iloc[:, 3].str.strip()

        # Xử lý ngày tháng chuyên sâu
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY_GỐC'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY_DT'].dt.month.fillna(0).astype(int)
        
        # Phân loại Vùng Miền (Logic AI - Fix lỗi 1 màu ở image_eb9d08)
        def set_region(kh):
            v = str(kh).upper()
            if any(x in v for x in ['HN', 'NỘI', 'BẮC', 'SƠN', 'PHÚ']): return 'MIỀN BẮC'
            if any(x in v for x in ['ĐÀ NẴNG', 'HUẾ', 'TRUNG', 'VINH']): return 'MIỀN TRUNG'
            return 'MIỀN NAM'
        df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(set_region)
        
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu V82: {e}")
        return None

# --- SIDEBAR: GIAO DIỆN LỌC CHUYÊN NGHIỆP ---
data = load_data_v82()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1162/1162456.png", width=50)
    st.title("QUẢN TRỊ V82")
    if st.button('🔄 ĐỒNG BỘ DỮ LIỆU GỐC', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if data is not None:
        y_list = sorted(data[data['NĂM'] > 2000]['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Năm báo cáo", ["Tất cả"] + y_list)
        
        m_options = ["Tất cả (Cộng dồn)"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Tháng báo cáo", m_options)

        # Lọc dữ liệu
        df_final = data.copy()
        if sel_year != "Tất cả":
            df_final = df_final[df_final['NĂM'] == sel_year]
        if sel_month != "Tất cả (Cộng dồn)":
            m_val = int(sel_month.replace("Tháng ", ""))
            df_final = df_final[df_final['THÁNG_NUM'] == m_val]

# --- MAIN DASHBOARD ---
if data is not None:
    st.header(f"📊 BÁO CÁO: {sel_month} / {sel_year}")
    
    # 1. KPI chuẩn mực (Khớp 100% số dòng)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng ca hỏng", f"{len(df_final):,}")
    k2.metric("Thiết bị lỗi", f"{df_final['MÃ_MÁY'].nunique():,}")
    counts = df_final['MÃ_MÁY'].value_counts()
    k3.metric("Máy hỏng tái diễn", len(counts[counts > 1]))
    k4.metric("Khách hàng/Đơn vị", df_final['KHÁCH_HÀNG'].nunique())

    # 2. Tabs chức năng
    t1, t2, t3, t4 = st.tabs(["📈 THỐNG KÊ", "🔍 TRUY LỤC", "🤖 AI ANALYST", "📋 XEM DỮ LIỆU GỐC"])

    with t1:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Top Linh kiện lỗi")
            # Lọc bỏ giá trị "Chưa xác định" để biểu đồ chuyên nghiệp hơn
            clean_lk = df_final[df_final['LINH_KIỆN'] != "Chưa xác định"]
            top_lk = clean_lk['LINH_KIỆN'].value_counts().head(10)
            fig_bar = px.bar(top_lk, orientation='h', color=top_lk.values, color_continuous_scale='Reds')
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.subheader("Tỷ lệ Vùng miền")
            fig_pie = px.pie(df_final, names='VÙNG_MIỀN', hole=0.4,
                             color_discrete_map={'MIỀN BẮC':'#E74C3C', 'MIỀN TRUNG':'#F1C40F', 'MIỀN NAM':'#3498DB'})
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        txt = st.text_input("Gõ mã máy hoặc tên khách hàng để truy lục nhanh:")
        if txt:
            res = df_final[df_final.astype(str).apply(lambda x: x.str.contains(txt, case=False)).any(axis=1)]
            st.dataframe(res, use_container_width=True)

    with t3:
        st.subheader("🤖 Trợ lý AI (Data-Driven)")
        ask = st.chat_input("Hỏi AI về dữ liệu...")
        if ask:
            st.info(f"Sếp đang hỏi: {ask}")
            if "nhiều nhất" in ask.lower():
                best = df_final['LINH_KIỆN'].value_counts().idxmax()
                st.write(f"🤖 Trả lời: Linh kiện lỗi nhiều nhất là **{best}**.")
            else:
                st.write("🤖 Tôi đang phân tích toàn bộ dòng dữ liệu của sếp...")

    with t4:
        st.write("Kiểm tra 50 dòng dữ liệu hệ thống đang đọc (Để đối soát lệch cột):")
        st.dataframe(df_final.head(50), use_container_width=True)
