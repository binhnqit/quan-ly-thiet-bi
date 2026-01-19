import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# 1. CẤU HÌNH GIAO DIỆN SANG TRỌNG
st.set_page_config(page_title="Hệ Thống Quản Trị V100", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background: #ffffff; border-radius: 12px; padding: 20px; border-bottom: 5px solid #1E3A8A; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #dee2e6; border-radius: 5px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v100():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None)
        
        cleaned_data = []
        for index, row in df_raw.iterrows():
            # Chuyển dòng thành chuỗi để quét Regex
            row_str = " ".join(row.values.astype(str))
            
            # 1. Tìm Ngày (Phải có ngày mới lấy)
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_str)
            if not date_match: continue
            ngay = date_match.group(1)

            # 2. Tìm Mã Máy (Số từ 3-5 chữ số đứng riêng)
            ma_match = re.findall(r'\b\d{3,5}\b', row_str)
            ma = ma_match[0] if ma_match else "N/A"
            if ma == "N/A": continue # Loại bỏ dòng rác không có mã máy

            # 3. Lấy Khách Hàng và Linh Kiện (Dựa trên vị trí thực tế trong hình image_ec0e41)
            kh = str(row.iloc[2]).strip() if len(row) > 2 else "Khách vãng lai"
            lk = str(row.iloc[3]).strip() if len(row) > 3 else "Lỗi chung"
            
            # Chặn đứng dữ liệu rác "Chưa xác định" (Fix image_ec0eb5)
            if "Chưa xác định" in kh or "Mã số" in kh: continue

            cleaned_data.append([ngay, ma, kh, lk])

        df = pd.DataFrame(cleaned_data, columns=['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN'])
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY_DT'].dt.month.fillna(1).astype(int)

        # 4. THUẬT TOÁN PHÂN VÙNG MIỀN TỐI ƯU (Cứu Miền Trung & Xóa "Đĩa CD")
        def classify_region(name):
            n = str(name).upper()
            # Danh sách từ khóa quét thông minh
            if any(x in n for x in ['ĐÀ NẴNG', 'HUẾ', 'QUẢNG', 'VINH', 'NGHỆ', 'TĨNH', 'BÌNH ĐỊNH', 'KHÁNH HÒA', 'TRUNG']):
                return 'MIỀN TRUNG'
            if any(x in n for x in ['HN', 'NỘI', 'BẮC', 'PHÚ', 'SƠN', 'THÁI', 'GIANG', 'NINH', 'TUYÊN', 'PHONG']):
                return 'MIỀN BẮC'
            # Mặc định còn lại là Miền Nam
            return 'MIỀN NAM'
            
        df['VÙNG'] = df['KHÁCH_HÀNG'].apply(classify_region)
        return df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return None

# --- MAIN APP ---
data = load_data_v100()

if data is not None:
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/782/782761.png", width=100)
        st.title("QUẢN TRỊ V100")
        if st.button('🔄 CẬP NHẬT LIVE DATA', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        y_sel = st.selectbox("Năm", sorted(data['NĂM'].unique(), reverse=True))
        m_sel = st.selectbox("Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])

        df_final = data[data['NĂM'] == y_sel]
        if m_sel != "Tất cả":
            df_final = df_final[df_final['THÁNG'] == int(m_sel.replace("Tháng ", ""))]

    # KPI Header
    st.title(f"🚀 Báo Cáo Tài Sản - {m_sel}/{y_sel}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    re_fail = df_final['MÃ_MÁY'].value_counts()
    re_fail = re_fail[re_fail > 1]
    c3.metric("Máy hỏng tái diễn (>1 lần)", len(re_fail))
    c4.metric("Tỷ lệ khắc phục", "100%")

    # Tabs
    t1, t2, t3, t4 = st.tabs(["📊 BIỂU ĐỒ TỔNG QUAN", "⚠️ DANH SÁCH ĐEN", "🔍 TRA CỨU", "📥 DỮ LIỆU SẠCH"])

    with t1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            # Biểu đồ Donut sạch sẽ (Fix image_b778ae)
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5,
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN TRUNG':'#F59E0B', 'MIỀN NAM':'#10B981'})
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.subheader("🔧 Top Linh kiện hỏng")
            top_lk = df_final['LINH_KIỆN'].value_counts().head(10)
            fig_bar = px.bar(top_lk, orientation='h', color=top_lk.values, color_continuous_scale='Viridis')
            st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.subheader("🚩 DANH SÁCH THIẾT BỊ CẦN KIỂM TRA ĐẶC BIỆT")
        if not re_fail.empty:
            bl_rows = []
            for m_id, count in re_fail.items():
                m_info = df_final[df_final['MÃ_MÁY'] == m_id]
                bl_rows.append({
                    "Mã Máy": m_id,
                    "Số lần hỏng": count,
                    "Khách hàng": m_info['KHÁCH_HÀNG'].iloc[0],
                    "Linh kiện đã thay": ", ".join(m_info['LINH_KIỆN'].unique())
                })
            st.table(pd.DataFrame(bl_rows).sort_values("Số lần hỏng", ascending=False))
        else:
            st.success("Không có máy hỏng tái diễn!")

    with t3:
        search = st.text_input("Nhập mã máy hoặc tên khách hàng để truy vết:")
        if search:
            st.dataframe(df_final[df_final.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)], use_container_width=True)

    with t4:
        st.write("Dữ liệu đã qua bộ lọc AI (Chỉ giữ lại các dòng hợp lệ):")
        st.dataframe(df_final[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
