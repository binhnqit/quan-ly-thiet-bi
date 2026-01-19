import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# 1. THIẾT LẬP HỆ THỐNG EXECUTIVE
st.set_page_config(page_title="Hệ Thống Quản Trị V110", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #1E3A8A; font-weight: bold; }
    .stTable { font-size: 14px; }
    .status-critical { color: #d32f2f; font-weight: bold; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=60) # Tăng cache để mượt mà hơn
def load_and_optimize_data():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_rows = []
        for idx, row in df_raw.iterrows():
            # Skip header
            if idx == 0 or "Mã số" in str(row.iloc[1]): continue
            
            row_str = " ".join(row.values.astype(str))
            
            # 1. Regex bóc tách ngày tháng chuẩn
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_str)
            if not date_match: continue
            date_val = date_match.group(1)

            # 2. Định danh thiết bị (Ưu tiên cột 1, dự phòng Regex)
            ma = str(row.iloc[1]).strip().split('.')[0]
            if not ma or ma == "nan":
                ma_match = re.findall(r'\b\d{3,5}\b', row_str)
                ma = ma_match[0] if ma_match else "N/A"
            
            if ma == "N/A": continue

            # 3. Thông tin chi tiết
            kh = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            
            valid_rows.append([date_val, ma, kh, lk])

        df = pd.DataFrame(valid_rows, columns=['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN'])
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY_DT'].dt.month.fillna(1).astype(int)
        df['THÁNG_NĂM'] = df['NGÀY_DT'].dt.strftime('%m/%Y')

        # 4. Phân vùng miền tối ưu (Hard-mapping)
        def get_vung(name):
            n = str(name).upper()
            if any(x in n for x in ['ĐÀ NẴNG', 'HUẾ', 'QUẢNG', 'VINH', 'NGHỆ', 'TĨNH', 'BÌNH ĐỊNH', 'KHÁNH HÒA', 'TRUNG']):
                return 'MIỀN TRUNG'
            if any(x in n for x in ['HN', 'NỘI', 'BẮC', 'PHÚ', 'SƠN', 'THÁI', 'GIANG', 'NINH', 'TUYÊN']):
                return 'MIỀN BẮC'
            return 'MIỀN NAM'
        
        df['VÙNG'] = df['KHÁCH_HÀNG'].apply(get_vung)
        return df
    except Exception as e:
        st.error(f"Lỗi kiến trúc dữ liệu: {e}")
        return None

# --- KHỞI CHẠY HỆ THỐNG ---
data = load_and_optimize_data()

if data is not None:
    with st.sidebar:
        st.title("🛡️ QUẢN TRỊ V110")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        y_sel = st.selectbox("📅 Chọn Năm", sorted(data['NĂM'].unique(), reverse=True))
        m_sel = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])

        # Lọc dữ liệu lõi
        mask = (data['NĂM'] == y_sel)
        if m_sel != "Tất cả":
            mask &= (data['THÁNG'] == int(m_sel.replace("Tháng ", "")))
        df_view = data[mask]

    # --- DASHBOARD CHÍNH ---
    st.title(f"📊 Hệ Thống Phân Tích Lỗi Thiết Bị - {m_sel}/{y_sel}")
    
    # KPI SECTION
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng ca hỏng", f"{len(df_view):,}")
    k2.metric("Thiết bị lỗi", f"{df_view['MÃ_MÁY'].nunique():,}")
    
    counts = df_view['MÃ_MÁY'].value_counts()
    critical_devices = counts[counts >= 3] # Thiết bị hỏng cực nặng
    re_fail = counts[counts > 1] # Thiết bị hỏng tái diễn
    
    k3.metric("Hỏng tái diễn (>1 lần)", f"{len(re_fail)}", delta=f"{len(critical_devices)} Cực nặng", delta_color="inverse")
    k4.metric("Khách hàng báo lỗi", df_view['KHÁCH_HÀNG'].nunique())

    # TABULAR VIEW
    t1, t2, t3, t4 = st.tabs(["📉 XU HƯỚNG & PHÂN BỔ", "🚩 QUẢN TRỊ RỦI RO (RE-FAIL)", "🔍 TRUY XUẤT NHANH", "📋 DỮ LIỆU GỐC"])

    with t1:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("📈 Xu hướng lỗi theo thời gian")
            trend_data = df_view.groupby('NGÀY_DT').size().reset_index(name='Số ca hỏng')
            fig_trend = px.line(trend_data, x='NGÀY_DT', y='Số ca hỏng', markers=True, 
                                line_shape='spline', color_discrete_sequence=['#1E3A8A'])
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with c2:
            st.subheader("📍 Phân bổ Vùng Miền")
            fig_pie = px.pie(df_view, names='VÙNG', hole=0.5,
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN TRUNG':'#F59E0B', 'MIỀN NAM':'#10B981'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("🔧 Phân tích Linh kiện lỗi")
        top_lk = df_view['LINH_KIỆN'].value_counts().head(15).sort_values(ascending=True)
        fig_bar = px.bar(top_lk, orientation='h', text_auto=True, 
                         color=top_lk.values, color_continuous_scale='Blues')
        st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.subheader("⚠️ Danh sách thiết bị có rủi ro cao")
        if not re_fail.empty:
            bl_rows = []
            for m_id, count in re_fail.items():
                m_info = df_view[df_view['MÃ_MÁY'] == m_id]
                status = "🚨 CỰC NẶNG" if count >= 3 else "⚠️ CẢNH BÁO"
                bl_rows.append({
                    "Mã Máy": m_id,
                    "Tình trạng": status,
                    "Số lần hỏng": count,
                    "Đơn vị sử dụng": m_info['KHÁCH_HÀNG'].iloc[0],
                    "Linh kiện đã thay": " | ".join(m_info['LINH_KIỆN'].unique())
                })
            st.dataframe(pd.DataFrame(bl_rows).sort_values("Số lần hỏng", ascending=False), 
                         use_container_width=True, hide_index=True)
        else:
            st.success("Hệ thống vận hành tốt, chưa ghi nhận máy hỏng tái diễn.")

    with t3:
        search_col1, search_col2 = st.columns([1, 2])
        with search_col1:
            search_query = st.text_input("🔍 Nhập Mã máy hoặc Tên đơn vị:")
        if search_query:
            results = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            st.write(f"Tìm thấy {len(results)} bản ghi phù hợp:")
            st.table(results[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']])

    with t4:
        st.write(f"Toàn bộ {len(df_view)} bản ghi đã được làm sạch và chuẩn hóa:")
        st.dataframe(df_view, use_container_width=True, hide_index=True)
