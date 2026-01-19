import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị V90", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background: #ffffff; border-radius: 10px; padding: 15px; border-top: 4px solid #1E3A8A; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { background-color: #e9ecef; border-radius: 10px; padding: 5px; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v90():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu và bỏ qua các dòng hoàn toàn trống
        df_raw = pd.read_csv(url, dtype=str, header=None).dropna(how='all')
        
        final_rows = []
        for _, row in df_raw.iterrows():
            row_str = " ".join(row.values.astype(str))
            # Loại bỏ dòng tiêu đề và các dòng "Chưa xác định" rác
            if any(x in row_str for x in ["Mã số", "Ngày", "MÃ_MÁY", "KHÁCH_HÀNG"]): continue
            
            # Dùng Regex bóc tách để tránh lệch cột (image_ec0e96)
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_str)
            ngay = date_match.group(1) if date_match else "01/01/2026"
            
            # Mã máy (số từ 3-5 chữ số)
            ma_match = re.findall(r'\b\d{3,5}\b', row_str)
            ma = ma_match[0] if ma_match else "N/A"
            
            # Cố định vị trí Khách hàng và Linh kiện
            kh = str(row.iloc[2]).strip() if len(row) > 2 else "Không xác định"
            lk = str(row.iloc[3]).strip() if len(row) > 3 else "Không có thông tin"
            
            # Chỉ lấy dòng có dữ liệu thực sự
            if ma != "N/A" and kh != "Chưa xác định":
                final_rows.append([ngay, ma, kh, lk])

        df = pd.DataFrame(final_rows, columns=['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN'])
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY_DT'].dt.month.fillna(0).astype(int)
        
        # PHÂN LOẠI VÙNG MIỀN THÔNG MINH (Cứu Miền Trung)
        def set_region(name):
            n = str(name).upper()
            bac = ['HN', 'NỘI', 'BẮC', 'PHÚ', 'SƠN', 'THÁI', 'TUYÊN', 'GIANG', 'NINH']
            trung = ['ĐÀ NẴNG', 'HUẾ', 'TRUNG', 'QUẢNG', 'VINH', 'NGHỆ', 'BÌNH ĐỊNH', 'KHÁNH HÒA']
            if any(x in n for x in bac): return 'BẮC'
            if any(x in n for x in trung): return 'TRUNG'
            return 'NAM'
            
        df['VÙNG'] = df['KHÁCH_HÀNG'].apply(set_region)
        return df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return None

# --- XỬ LÝ DỮ LIỆU ---
data = load_data_v90()

if data is not None:
    with st.sidebar:
        st.title("⚙️ ĐIỀU KHIỂN")
        if st.button('🔄 LÀM MỚI DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_y = st.selectbox("Năm", y_list)
        m_list = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Tháng", m_list)

        df_view = data[data['NĂM'] == sel_y]
        if sel_m != "Tất cả":
            df_view = df_view[df_view['THÁNG'] == int(sel_m.replace("Tháng ", ""))]

    # --- HIỂN THỊ ---
    st.header(f"📊 BÁO CÁO TỔNG QUAN {sel_m}/{sel_y}")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng ca hỏng", f"{len(df_view):,}")
    k2.metric("Số thiết bị lỗi", f"{df_view['MÃ_MÁY'].nunique():,}")
    
    counts = df_view['MÃ_MÁY'].value_counts()
    re_fail_df = counts[counts > 1]
    k3.metric("Máy hỏng tái diễn", len(re_fail_df))
    k4.metric("Vùng miền", df_view['VÙNG'].nunique())

    t1, t2, t3, t4 = st.tabs(["📈 THỐNG KÊ", "🚩 DANH SÁCH ĐEN (RE-FAIL)", "🔍 TRA CỨU", "📋 DỮ LIỆU SẠCH"])

    with t1:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Top Linh kiện lỗi")
            # Sạch hóa linh kiện lỗi để biểu đồ đẹp (image_ec0eb5)
            clean_lk = df_view[~df_view['LINH_KIỆN'].str.contains("Chưa|Không", na=False)]
            top_lk = clean_lk['LINH_KIỆN'].value_counts().head(10)
            fig_bar = px.bar(top_lk, orientation='h', color=top_lk.values, color_continuous_scale='Reds')
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.subheader("Tỷ trọng Vùng miền")
            fig_pie = px.pie(df_view, names='VÙNG', hole=0.4, 
                             color_discrete_map={'BẮC':'#1E3A8A', 'TRUNG':'#F59E0B', 'NAM':'#10B981'})
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        st.subheader("⚠️ CẢNH BÁO THIẾT BỊ HỎNG NHIỀU LẦN")
        if not re_fail_df.empty:
            black_list = []
            for m_id, count in re_fail_df.items():
                m_data = df_view[df_view['MÃ_MÁY'] == m_id]
                black_list.append({
                    "Mã Máy": m_id,
                    "Lần hỏng": count,
                    "Khách hàng": m_data['KHÁCH_HÀNG'].iloc[0],
                    "Chi tiết lỗi": " | ".join(m_data['LINH_KIỆN'].unique())
                })
            st.dataframe(pd.DataFrame(black_list), use_container_width=True)
        else:
            st.success("Tuyệt vời! Không có máy nào hỏng tái diễn.")

    with t3:
        search = st.text_input("Nhập mã máy hoặc tên khách hàng:")
        if search:
            res = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            st.table(res[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN']])

    with t4:
        st.write("Dữ liệu sau khi đã được AI lọc bỏ các dòng rác:")
        st.dataframe(df_view[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
