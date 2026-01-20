import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- 1. CẤU HÌNH HỆ THỐNG (GIỮ NGUYÊN) ---
st.set_page_config(page_title="Hệ Thống Quản Trị V15.000 - Final", layout="wide")

@st.cache_data(ttl=2)
def load_data_final_v15():
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

df = load_data_final_v15()

if not df.empty:
    # --- 2. SIDEBAR (BỔ SUNG NÚT XUẤT EXCEL) ---
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

        st.write("---")
        # CHỐT HẠ 1: TÍNH NĂNG XUẤT BÁO CÁO
        st.subheader("📥 Xuất dữ liệu sạch")
        towrite = BytesIO()
        df_final.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="🚀 Tải Excel Báo Cáo", data=towrite.getvalue(), file_name=f"Bao_cao_thiet_bi_{sel_year}.xlsx", mime="application/vnd.ms-excel")

    st.markdown(f"## 🛡️ HỆ THỐNG QUẢN TRỊ CHIẾN LƯỢC V15.000")
    
    # --- 3. TABS (GIỮ NGUYÊN VÀ BỔ SUNG NỘI DUNG VÀO T1) ---
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "📊 PHÂN TÍCH XU HƯỚNG", "💰 TÀI CHÍNH CHI TIẾT", 
        "🤖 TRỢ LÝ AI", "📁 DỮ LIỆU SẠCH", 
        "🩺 SỨC KHỎE & THANH LÝ", "🔮 DỰ BÁO & CẢNH BÁO"
    ])

    with t1:
        # Giữ nguyên 3 cột cũ, thêm hàng mới phía dưới cho CHỐT HẠ 2
        c_tr, c_pi, c_to = st.columns([1.5, 1, 1])
        with c_tr:
            m_t = df_y.groupby('THÁNG').size().reset_index(name='Số ca')
            st.plotly_chart(px.bar(m_t, x='THÁNG', y='Số ca', text_auto=True, color_discrete_sequence=['#007AFF']), use_container_width=True)
        with c_pi:
            st.plotly_chart(px.pie(df_final['VÙNG'].value_counts().reset_index(), values='count', names='VÙNG', hole=0.5), use_container_width=True)
        with c_to:
            st.plotly_chart(px.bar(df_final['MÃ_MÁY'].value_counts().head(10).reset_index(), x='count', y='MÃ_MÁY', orientation='h', text_auto=True), use_container_width=True)
        
        st.write("---")
        # CHỐT HẠ 2: SO SÁNH HIỆU QUẢ VÙNG MIỀN
        st.subheader("🌐 So sánh hiệu quả quản trị theo Vùng")
        region_comp = df_final.groupby('VÙNG').agg({'CP_THUC_TE': 'mean', 'MÃ_MÁY': 'count'}).reset_index()
        region_comp.columns = ['Vùng', 'Chi phí TB/Ca', 'Tổng số ca']
        fig_reg = px.scatter(region_comp, x='Tổng số ca', y='Chi phí TB/Ca', size='Tổng số ca', color='Vùng', text='Vùng', title="Tương quan Số ca và Chi phí trung bình mỗi Miền")
        st.plotly_chart(fig_reg, use_container_width=True)

    # CÁC TABS T2, T3, T4, T5, T6 GIỮ NGUYÊN LOGIC V14 (Không thay đổi)
    with t2:
        cost_data = df_final.groupby('LINH_KIỆN')[['CP_DU_KIEN', 'CP_THUC_TE']].sum().reset_index()
        st.plotly_chart(px.bar(cost_data, x='LINH_KIỆN', y=['CP_DU_KIEN', 'CP_THUC_TE'], barmode='group'), use_container_width=True)
    with t3: st.info(f"AI: Máy {df_final['MÃ_MÁY'].value_counts().idxmax()} cần kiểm tra bảo trì gấp.")
    with t4: st.dataframe(df_final, use_container_width=True)
    with t5: 
        h_db = df.groupby('MÃ_MÁY').agg({'NGÀY': 'count', 'CP_THUC_TE': 'sum'}).reset_index()
        st.dataframe(h_db.sort_values('NGÀY', ascending=False), use_container_width=True)
    with t6:
        st.subheader("🔮 Dự báo nhu cầu & Cảnh báo sớm")
        # Giữ nguyên logic cảnh báo 60 ngày từ V14
        df_sorted = df.sort_values(['MÃ_MÁY', 'NGÀY'])
        df_sorted['KHOANG_CACH'] = df_sorted.groupby('MÃ_MÁY')['NGÀY'].diff().dt.days
        warnings = df_sorted[df_sorted['KHOANG_CACH'] <= 60]
        if not warnings.empty: st.warning(f"Cảnh báo: {len(warnings)} ca hỏng lặp lại trong thời gian ngắn!")
        st.write("Dự báo linh kiện tháng tới:", (df['LINH_KIỆN'].value_counts() / (len(df['NĂM'].unique())*12)).round(1).head(5))

else:
    st.info("Hệ thống đã sẵn sàng. Vui lòng kiểm tra dữ liệu đầu vào.")
