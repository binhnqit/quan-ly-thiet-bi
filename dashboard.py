import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Quản Trị V13.000", layout="wide")

@st.cache_data(ttl=2)
def load_data_expert_v13():
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

# --- 2. XỬ LÝ DỮ LIỆU ---
df = load_data_expert_v13()

if not df.empty:
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

    # --- 3. GIAO DIỆN CHÍNH ---
    st.markdown(f"## 🛡️ BÁO CÁO QUẢN TRỊ THIẾT BỊ V13.000 - {sel_year}")
    
    # HÀNG KPI (GIỮ NGUYÊN)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng ca hỏng", f"{len(df_final)} ca")
    m2.metric("Số máy hỏng", f"{df_final['MÃ_MÁY'].nunique()} máy")
    m3.metric("Tổng chi phí thực", f"{df_final['CP_THUC_TE'].sum():,.0f} đ")
    cl = df_final['CHENH_LECH'].sum()
    m4.metric("Chênh lệch ngân sách", f"{cl:,.0f} đ", delta=f"{cl:,.0f}", delta_color="inverse")

    # --- 4. CÁC TABS CHỨC NĂNG ---
    t1, t2, t3, t4, t5 = st.tabs(["📊 PHÂN TÍCH XU HƯỚNG", "💰 TÀI CHÍNH CHI TIẾT", "🤖 TRỢ LÝ AI", "📁 DỮ LIỆU SẠCH", "🩺 SỨC KHỎE & THANH LÝ"])

    with t1:
        # Layout 3 cột như hình ảnh gợi ý
        col_trend, col_pie, col_top = st.columns([1.5, 1, 1])
        
        with col_trend:
            st.subheader("📈 Xu hướng tháng")
            monthly_trend = df_y.groupby('THÁNG').size().reset_index(name='Số ca')
            fig_trend = px.bar(monthly_trend, x='THÁNG', y='Số ca', text_auto=True, color_discrete_sequence=['#007AFF'])
            fig_trend.update_layout(height=400)
            st.plotly_chart(fig_trend, use_container_width=True)

        with col_pie:
            st.subheader("📍 Tỷ lệ Miền")
            vung_data = df_final['VÙNG'].value_counts().reset_index()
            fig_pie = px.pie(vung_data, values='count', names='VÙNG', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_top:
            st.subheader("🚩 Top 10 Thiết bị lỗi")
            top_device = df_final['MÃ_MÁY'].value_counts().head(10).reset_index()
            top_device.columns = ['Mã Máy', 'Số lần']
            fig_top = px.bar(top_device, x='Số lần', y='Mã Máy', orientation='h', text_auto=True, color='Số lần', color_continuous_scale='Reds')
            fig_top.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_top, use_container_width=True)

    with t2:
        st.subheader("💰 Đối soát chi phí Dự kiến vs Thực tế")
        cost_data = df_final.groupby('LINH_KIỆN')[['CP_DU_KIEN', 'CP_THUC_TE']].sum().reset_index()
        fig_cost = go.Figure(data=[
            go.Bar(name='Dự kiến', x=cost_data['LINH_KIỆN'], y=cost_data['CP_DU_KIEN'], marker_color='#A2A2A2'),
            go.Bar(name='Thực tế', x=cost_data['LINH_KIỆN'], y=cost_data['CP_THUC_TE'], marker_color='#007AFF')
        ])
        fig_cost.update_layout(barmode='group')
        st.plotly_chart(fig_cost, use_container_width=True)

    with t3:
        st.subheader("🤖 Trợ lý AI - Nhận định dữ liệu")
        if not df_final.empty:
            st.info(f"Phân tích nhanh: Máy **{df_final['MÃ_MÁY'].value_counts().idxmax()}** đang có tần suất hỏng cao nhất tại miền **{df_final['VÙNG'].value_counts().idxmax()}**.")

    with t4:
        st.subheader("📁 Bảng đối soát Master")
        st.dataframe(df_final, use_container_width=True)

    with t5:
        st.subheader("🩺 Tình trạng sức khỏe & Gợi ý thanh lý")
        health_db = df.groupby('MÃ_MÁY').agg({'NGÀY': 'count', 'CP_THUC_TE': 'sum'}).rename(columns={'NGÀY': 'Số lần hỏng', 'CP_THUC_TE': 'Tổng chi phí'})
        def check(row): return "🔴 THANH LÝ" if row['Số lần hỏng'] >= 4 else ("🟡 THEO DÕI" if row['Số lần hỏng'] == 3 else "🟢 TỐT")
        health_db['ĐÁNH GIÁ'] = health_db.apply(check, axis=1)
        st.dataframe(health_db.sort_values('Số lần hỏng', ascending=False), use_container_width=True)

else:
    st.warning("Hệ thống đang chờ dữ liệu hợp lệ từ Master Key.")
