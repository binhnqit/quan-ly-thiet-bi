import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# 1. CẤU HÌNH GIAO DIỆN EXECUTIVE
st.set_page_config(page_title="Hệ Thống Quản Trị V105", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background: white; border-radius: 12px; padding: 15px; border-left: 6px solid #1E3A8A; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; border-radius: 10px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v105():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu thô (giống V101)
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            row_str = " ".join(row.values.astype(str))
            # Bỏ dòng tiêu đề
            if i == 0 or "Mã số" in row_str or "Ngày" in row_str: continue
            
            # LOGIC LẤY DỮ LIỆU TỪ V101 (ĐÃ KIỂM CHỨNG)
            # Dùng regex tìm ngày
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_str)
            ngay = date_match.group(1) if date_match else "01/01/2026"
            
            # Lấy mã máy, khách hàng, linh kiện theo vị trí cột cố định
            ma = str(row.iloc[1]).strip().split('.')[0]
            kh = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            
            # Chỉ lấy nếu có Mã Máy (Chặn dòng rác)
            if ma and ma != "nan":
                final_rows.append([ngay, ma, kh, lk])

        df = pd.DataFrame(final_rows, columns=['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN'])
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY_DT'].dt.month.fillna(0).astype(int)
        
        # PHÂN LOẠI MIỀN (CỨU MIỀN TRUNG)
        def set_vung(kh):
            v = str(kh).upper()
            if any(x in v for x in ['ĐÀ NẴNG', 'HUẾ', 'TRUNG', 'QUẢNG', 'VINH', 'NGHỆ', 'BÌNH ĐỊNH', 'KHÁNH HÒA']): 
                return 'MIỀN TRUNG'
            if any(x in v for x in ['HN', 'BẮC', 'SƠN', 'PHÚ', 'THÁI', 'GIANG', 'NINH', 'TUYÊN', 'NỘI']): 
                return 'MIỀN BẮC'
            return 'MIỀN NAM'
        
        df['VÙNG'] = df['KHÁCH_HÀNG'].apply(set_vung)
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None

# --- SIDEBAR: ĐIỀU KHIỂN CHUYÊN NGHIỆP ---
data = load_data_v105()

if data is not None:
    with st.sidebar:
        st.title("🛡️ QUẢN TRỊ TÀI SẢN")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU MỚI', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        st.divider()
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_y = st.selectbox("📅 Năm báo cáo", ["Tất cả"] + [int(y) for y in y_list if y > 2000])
        
        m_list = ["Tất cả (Cộng dồn)"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("📆 Tháng báo cáo", m_list)

        # Logic lọc
        df_filtered = data.copy()
        if sel_y != "Tất cả": df_filtered = df_filtered[df_filtered['NĂM'] == sel_y]
        if sel_m != "Tất cả (Cộng dồn)":
            df_filtered = df_filtered[df_filtered['THÁNG'] == int(sel_m.replace("Tháng ", ""))]

    # --- DASHBOARD ---
    st.markdown(f"### 📊 Báo cáo: {sel_m} / {sel_y}")
    
    # KPI 
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng ca hỏng", f"{len(df_filtered):,}")
    k2.metric("Số thiết bị lỗi", f"{df_filtered['MÃ_MÁY'].nunique():,}")
    
    # Máy hỏng tái diễn (logic mới)
    re_counts = df_filtered['MÃ_MÁY'].value_counts()
    black_list = re_counts[re_counts > 1]
    k3.metric("Máy hỏng tái diễn", len(black_list))
    k4.metric("Số đơn vị/KH", df_filtered['KHÁCH_HÀNG'].nunique())

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📉 THỐNG KÊ", "🚩 DANH SÁCH ĐEN", "🔍 TRA CỨU", "🤖 AI ASSISTANT"])

    with tab1:
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.write("**Top 10 Linh kiện lỗi phổ biến**")
            top_lk = df_filtered['LINH_KIỆN'].value_counts().head(10)
            st.bar_chart(top_lk)
        with c_right:
            st.write("**Phân bổ theo Vùng miền**")
            fig = px.pie(df_filtered, names='VÙNG', hole=0.4,
                         color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN TRUNG':'#F59E0B', 'MIỀN NAM':'#10B981'})
            st.plotly_chart(fig, use_container_width=True)
            

    with tab2:
        st.subheader("⚠️ Danh sách máy hỏng tái diễn (>1 lần)")
        if not black_list.empty:
            bl_data = []
            for m_id, count in black_list.items():
                m_info = df_filtered[df_filtered['MÃ_MÁY'] == m_id]
                bl_data.append({
                    "Mã Máy": m_id,
                    "Số lần hỏng": count,
                    "Khách hàng cuối": m_info['KHÁCH_HÀNG'].iloc[0],
                    "Các lỗi đã gặp": " | ".join(m_info['LINH_KIỆN'].unique())
                })
            st.table(pd.DataFrame(bl_data).sort_values("Số lần hỏng", ascending=False))
        else:
            st.success("Không ghi nhận máy hỏng tái diễn trong kỳ báo cáo này.")

    with tab3:
        search = st.text_input("Gõ mã máy hoặc tên khách hàng để truy xuất nhanh:")
        if search:
            res = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            st.dataframe(res, use_container_width=True)

    with tab4:
        st.subheader("🤖 Trợ lý AI Assistant (Dữ liệu Live)")
        ask = st.chat_input("Hỏi tôi về tình hình hỏng hóc...")
        if ask:
            st.write(f"💬 **Sếp hỏi:** {ask}")
            if "nhiều nhất" in ask.lower():
                best = df_filtered['LINH_KIỆN'].value_counts().idxmax()
                st.info(f"🤖 Trả lời: Linh kiện **{best}** đang là vấn đề lớn nhất với {df_filtered['LINH_KIỆN'].value_counts().max()} ca hỏng.")
            else:
                st.info("🤖 Tôi đã nhận lệnh. Tôi sẽ phân tích dựa trên toàn bộ dữ liệu sạch hiện có.")
