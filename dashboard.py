import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP
st.set_page_config(page_title="HỆ THỐNG QUẢN TRỊ TÀI SẢN 2026", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background: white; border-radius: 12px; padding: 15px; border-top: 5px solid #1E3A8A; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_clean_data_2026():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            row_content = " ".join(row.values.astype(str))
            if i == 0 or "Mã số" in row_content: continue
            
            # --- TRUY XUẤT THÔNG TIN ---
            ngay_str = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip().split('.')[0]
            khach_hang = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip() # Cột F

            if not ma_may or ma_may == "nan": continue

            # Xử lý ngày tháng (Dữ liệu đã được sếp chuẩn hóa)
            dt = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
            if pd.notnull(dt) and dt.year == 2026:
                final_rows.append({
                    "NGÀY": ngay_str,
                    "THÁNG": dt.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": khach_hang,
                    "LINH_KIỆN": linh_kien,
                    "VÙNG": vung_mien.upper()
                })

        df = pd.DataFrame(final_rows)
        # Chuẩn hóa tên vùng miền để đồng nhất biểu đồ
        df['VÙNG'] = df['VÙNG'].replace({
            'MIỀN BẮC': 'MIỀN BẮC', 'BẮC': 'MIỀN BẮC', 'MB': 'MIỀN BẮC',
            'MIỀN TRUNG': 'MIỀN TRUNG', 'TRUNG': 'MIỀN TRUNG', 'MT': 'MIỀN TRUNG',
            'MIỀN NAM': 'MIỀN NAM', 'NAM': 'MIỀN NAM', 'MN': 'MIỀN NAM'
        })
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- THỰC THI ---
data = load_clean_data_2026()

if data is not None:
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1063/1063200.png", width=100)
        st.title("QUẢN TRỊ V140")
        if st.button('🔄 CẬP NHẬT LIVE DATA', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_m = st.selectbox("Chọn tháng báo cáo", ["Tất cả các tháng"] + [f"Tháng {i}" for i in range(1, 13)])

    # Lọc dữ liệu theo tháng
    df_final = data.copy()
    if sel_m != "Tất cả các tháng":
        m_num = int(sel_m.replace("Tháng ", ""))
        df_final = df_final[df_final['THÁNG'] == m_num]

    # --- HEADER & KPI ---
    st.title(f"🚀 Báo Cáo Tài Sản 2026 - {sel_m}")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TỔNG CA HỎNG", len(df_final))
    k2.metric("MIỀN BẮC", len(df_final[df_final['VÙNG'] == 'MIỀN BẮC']))
    k3.metric("MIỀN TRUNG", len(df_final[df_final['VÙNG'] == 'MIỀN TRUNG']))
    k4.metric("MIỀN NAM", len(df_final[df_final['VÙNG'] == 'MIỀN NAM']))

    # --- TABS NỘI DUNG ---
    tab1, tab2, tab3 = st.tabs(["📉 BIỂU ĐỒ TỔNG KẾT", "🚩 DANH SÁCH RE-FAIL", "🔍 TRA CỨU CHI TIẾT"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5,
                             color='VÙNG', color_discrete_map={
                                 'MIỀN BẮC': '#1E3A8A', 
                                 'MIỀN TRUNG': '#EF4444', 
                                 'MIỀN NAM': '#10B981'
                             })
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("🔧 Top 10 Linh kiện lỗi")
            top_lk = df_final['LINH_KIỆN'].value_counts().head(10).reset_index()
            fig_bar = px.bar(top_lk, x='count', y='LINH_KIỆN', orientation='h',
                             labels={'count': 'Số lần hỏng', 'LINH_KIỆN': 'Linh kiện'},
                             color='count', color_continuous_scale='Blues')
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("⚠️ Máy hỏng tái diễn (Trên 1 lần)")
        re_fail = df_final['MÃ_MÁY'].value_counts()
        re_fail = re_fail[re_fail > 1]
        
        if not re_fail.empty:
            list_rf = []
            for m_id, count in re_fail.items():
                m_data = df_final[df_final['MÃ_MÁY'] == m_id]
                list_rf.append({
                    "Mã Máy": m_id,
                    "Số lần hỏng": count,
                    "Khách hàng": m_data['KHÁCH_HÀNG'].iloc[0],
                    "Vùng": m_data['VÙNG'].iloc[0],
                    "Linh kiện đã thay": " | ".join(m_data['LINH_KIỆN'].unique())
                })
            st.dataframe(pd.DataFrame(list_rf), use_container_width=True)
        else:
            st.success("Tuyệt vời! Không có máy nào hỏng tái diễn trong kỳ báo cáo này.")

    with tab3:
        st.subheader("📋 Dữ liệu sạch 2026")
        search_term = st.text_input("Gõ mã máy hoặc tên khách hàng để tìm nhanh:")
        if search_term:
            df_search = df_final[df_final.apply(lambda row: search_term.lower() in row.astype(str).str.lower().values, axis=1)]
            st.dataframe(df_search, use_container_width=True)
        else:
            st.dataframe(df_final, use_container_width=True)
