import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. CẤU HÌNH HỆ THỐNG (GIỮ NGUYÊN) ---
st.set_page_config(page_title="Hệ Thống Quản Trị V14.000", layout="wide")

@st.cache_data(ttl=2)
def load_data_v14():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    try:
        df_raw = pd.read_csv(url, dtype=str, header=None, skiprows=1).fillna("0")
        clean_data = []
        for i, row in df_raw.iterrows():
            ma_may = str(row.iloc[1]).strip()
            if not ma_may or len(ma_may) < 2 or "MÃ" in ma_may.upper(): continue
            ngay_raw = str(row.iloc[6]).strip()
            p_date = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(p_date):
                cp_dk = pd.to_numeric(str(row.iloc[7]).replace(',', ''), errors='coerce') or 0
                cp_tt = pd.to_numeric(str(row.iloc[8]).replace(',', ''), errors='coerce') or 0
                clean_data.append({
                    "NGÀY": p_date, "NĂM": p_date.year, "THÁNG": p_date.month,
                    "MÃ_MÁY": ma_may, "KHÁCH_HÀNG": str(row.iloc[2]).strip(),
                    "LINH_KIỆN": str(row.iloc[3]).strip(), "VÙNG": str(row.iloc[5]).strip(),
                    "CP_DU_KIEN": cp_dk, "CP_THUC_TE": cp_tt, "CHENH_LECH": cp_tt - cp_dk
                })
        return pd.DataFrame(clean_data)
    except: return pd.DataFrame()

df = load_data_v14()

if not df.empty:
    # --- 2. SIDEBAR (GIỮ NGUYÊN) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3208/3208726.png", width=80)
        st.title("EXECUTIVE HUB")
        if st.button('🔄 ĐỒNG BỘ HỆ THỐNG'):
            st.cache_data.clear()
            st.rerun()
        sel_year = st.selectbox("📅 Năm báo cáo", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.multiselect("🗓️ Lọc Tháng", sorted(df_y['THÁNG'].unique()), default=sorted(df_y['THÁNG'].unique()))
        df_final = df_y[df_y['THÁNG'].isin(sel_month)]

    st.markdown(f"## 🛡️ QUẢN TRỊ THIẾT BỊ V14.000")
    
    # --- 3. TABS (BỔ SUNG TAB 6) ---
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "📊 PHÂN TÍCH XU HƯỚNG", "💰 TÀI CHÍNH CHI TIẾT", 
        "🤖 TRỢ LÝ AI", "📁 DỮ LIỆU SẠCH", 
        "🩺 SỨC KHỎE & THANH LÝ", "🔮 DỰ BÁO & CẢNH BÁO"
    ])

    # [Nội dung T1-T5 giữ nguyên như bản V13.000 để đảm bảo ổn định]
    with t1:
        c_tr, c_pi, c_to = st.columns([1.5, 1, 1])
        with c_tr:
            m_t = df_y.groupby('THÁNG').size().reset_index(name='Số ca')
            st.plotly_chart(px.bar(m_t, x='THÁNG', y='Số ca', text_auto=True, color_discrete_sequence=['#007AFF']), use_container_width=True)
        with c_pi:
            st.plotly_chart(px.pie(df_final['VÙNG'].value_counts().reset_index(), values='count', names='VÙNG', hole=0.5), use_container_width=True)
        with c_to:
            st.plotly_chart(px.bar(df_final['MÃ_MÁY'].value_counts().head(10).reset_index(), x='count', y='MÃ_MÁY', orientation='h', text_auto=True), use_container_width=True)

    with t2:
        cost_data = df_final.groupby('LINH_KIỆN')[['CP_DU_KIEN', 'CP_THUC_TE']].sum().reset_index()
        st.plotly_chart(px.bar(cost_data, x='LINH_KIỆN', y=['CP_DU_KIEN', 'CP_THUC_TE'], barmode='group'), use_container_width=True)

    with t3:
        st.info("Trợ lý AI đang sẵn sàng tại Tab 6 cho các dự báo chuyên sâu.")

    with t4: st.dataframe(df_final, use_container_width=True)

    with t5:
        h_db = df.groupby('MÃ_MÁY').agg({'NGÀY': 'count', 'CP_THUC_TE': 'sum'}).reset_index()
        st.dataframe(h_db.sort_values('NGÀY', ascending=False), use_container_width=True)

    # --- 4. MODULE MỚI: TAB 6 DỰ BÁO & CẢNH BÁO ---
    with t6:
        st.header("🔮 Hệ Thống Dự Báo Thông Minh")
        
        # MODULE 1: CẢNH BÁO SỚM (MÁY HỎNG DÀY ĐẶC)
        st.subheader("⚠️ 1. Cảnh báo rủi ro hỏng dày đặc (Trong 60 ngày)")
        df_sorted = df.sort_values(['MÃ_MÁY', 'NGÀY'])
        df_sorted['KHOANG_CACH'] = df_sorted.groupby('MÃ_MÁY')['NGÀY'].diff().dt.days
        warnings = df_sorted[df_sorted['KHOANG_CACH'] <= 60]
        if not warnings.empty:
            st.warning(f"Phát hiện {len(warnings)} trường hợp máy hỏng lại quá nhanh!")
            st.dataframe(warnings[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'KHOANG_CACH']].rename(columns={'KHOANG_CACH': 'Số ngày hỏng lại'}), use_container_width=True)
        else:
            st.success("Không có máy nào hỏng dày đặc.")

        # MODULE 2: DỰ BÁO LINH KIỆN (INVENTORY PROJECTION)
        st.subheader("📦 2. Dự báo nhu cầu linh kiện tháng tới")
        lk_stats = df['LINH_KIỆN'].value_counts()
        avg_lk = (lk_stats / len(df['NĂM'].unique()) / 12).round(1)
        
        col_inv1, col_inv2 = st.columns([2, 1])
        with col_inv1:
            fig_inv = px.bar(avg_lk.head(5), title="Số lượng linh kiện dự phòng cần/tháng", labels={'value': 'Số lượng dự kiến', 'index': 'Linh kiện'}, color_discrete_sequence=['#FF8C00'])
            st.plotly_chart(fig_inv, use_container_width=True)
        with col_inv2:
            st.write("**Gợi ý kho bãi:**")
            for lk, val in avg_lk.head(5).items():
                st.write(f"- **{lk}**: Chuẩn bị tối thiểu {int(val + 1)} đơn vị")

        # MODULE 3: ĐÁNH GIÁ VÒNG ĐỜI (SỨC KHỎE TỔNG THỂ)
        st.subheader("📉 3. Phân tích vòng đời thiết bị")
        # Giả lập tính toán tuổi đời dựa trên lần hỏng đầu tiên thấy trong data
        lifecycle = df.groupby('MÃ_MÁY').agg({'NGÀY': ['min', 'max', 'count']}).reset_index()
        lifecycle.columns = ['Mã Máy', 'Ngày đầu', 'Ngày cuối', 'Số lần hỏng']
        lifecycle['Tuổi đời ghi nhận (ngày)'] = (lifecycle['Ngày cuối'] - lifecycle['Ngày đầu']).dt.days
        
        fig_life = px.scatter
