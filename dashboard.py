import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CẤU HÌNH HỆ THỐNG QUẢN TRỊ ---
st.set_page_config(page_title="Hệ Thống Quản Trị Thiết Bị V10.000", layout="wide")

# GIỮ NGUYÊN CODE ĐỌC DỮ LIỆU ĐÃ CHẠY TỐT
@st.cache_data(ttl=2)
def load_data_enterprise():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    try:
        df_raw = pd.read_csv(url, dtype=str, header=None, skiprows=1).fillna("0")
        clean_data = []
        for i, row in df_raw.iterrows():
            ma_may = str(row.iloc[1]).strip()
            # MASTER KEY CHECK
            if not ma_may or len(ma_may) < 2 or "MÃ" in ma_may.upper(): continue

            ngay_raw = str(row.iloc[6]).strip()
            p_date = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            
            if pd.notnull(p_date):
                # Ép kiểu dữ liệu tài chính (Cột H và I)
                cp_dk = pd.to_numeric(str(row.iloc[7]).replace(',', ''), errors='coerce') or 0
                cp_tt = pd.to_numeric(str(row.iloc[8]).replace(',', ''), errors='coerce') or 0
                
                clean_data.append({
                    "NGÀY": p_date,
                    "NĂM": p_date.year,
                    "THÁNG": p_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": str(row.iloc[2]).strip(),
                    "LINH_KIỆN": str(row.iloc[3]).strip(),
                    "VÙNG": str(row.iloc[5]).strip(),
                    "CP_DU_KIEN": cp_dk,
                    "CP_THUC_TE": cp_tt,
                    "CHENH_LECH": cp_tt - cp_dk
                })
        return pd.DataFrame(clean_data)
    except: return pd.DataFrame()

# --- XỬ LÝ DỮ LIỆU ---
df = load_data_enterprise()

if not df.empty:
    # SIDEBAR CHUYÊN NGHIỆP
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

    # GIAO DIỆN CHÍNH
    st.markdown(f"## 🛡️ BÁO CÁO QUẢN TRỊ THIẾT BỊ {sel_year}")
    
    # 1. HÀNG KPI TÀI CHÍNH & VẬN HÀNH
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng ca hỏng", f"{len(df_final)} ca")
    m2.metric("Số máy hỏng", f"{df_final['MÃ_MÁY'].nunique()} máy")
    m3.metric("Tổng chi phí thực", f"{df_final['CP_THUC_TE'].sum():,.0f} đ")
    
    cl = df_final['CHENH_LECH'].sum()
    m4.metric("Chênh lệch ngân sách", f"{cl:,.0f} đ", delta=f"{cl:,.0f}", delta_color="inverse")

    # 2. CÁC TAB CHỨC NĂNG NÂNG CAO
    t1, t2, t3, t4 = st.tabs(["📊 PHÂN TÍCH XU HƯỚNG", "💰 TÀI CHÍNH CHI TIẾT", "🤖 TRỢ LÝ AI", "📁 DỮ LIỆU SẠCH"])

    with t1:
        st.subheader("📈 So sánh lượng máy hư qua các tháng")
        monthly_trend = df_y.groupby('THÁNG').size().reset_index(name='Số ca')
        # Tính toán tăng trưởng %
        monthly_trend['Tăng trưởng %'] = monthly_trend['Số ca'].pct_change() * 100
        
        fig_trend = px.bar(monthly_trend, x='THÁNG', y='Số ca', text_auto=True,
                           title=f"Số ca hỏng theo tháng năm {sel_year}",
                           color_discrete_sequence=['#007AFF'])
        st.plotly_chart(fig_trend, use_container_width=True)

    with t2:
        st.subheader("💰 Đối soát chi phí Dự kiến vs Thực tế")
        cost_data = df_final.groupby('LINH_KIỆN')[['CP_DU_KIEN', 'CP_THUC_TE']].sum().reset_index()
        fig_cost = go.Figure(data=[
            go.Bar(name='Dự kiến', x=cost_data['LINH_KIỆN'], y=cost_data['CP_DU_KIEN'], marker_color='#A2A2A2'),
            go.Bar(name='Thực tế', x=cost_data['LINH_KIỆN'], y=cost_data['CP_THUC_TE'], marker_color='#007AFF')
        ])
        fig_cost.update_layout(barmode='group', title="So sánh chi phí theo linh kiện")
        st.plotly_chart(fig_cost, use_container_width=True)

    with t3:
        st.subheader("🤖 Trợ lý AI - Nhận định dữ liệu")
        total_ca = len(df_final)
        top_may = df_final['MÃ_MÁY'].value_counts().idxmax()
        top_loi = df_final['LINH_KIỆN'].value_counts().idxmax()
        vung_max = df_final['VÙNG'].value_counts().idxmax()
        
        ai_msg = f"""
        **Nhận xét từ AI:**
        - Hệ thống ghi nhận **{total_ca}** vụ việc trong kỳ báo cáo.
        - Thiết bị cần chú ý nhất: **{top_may}** (Số lần lỗi cao nhất).
        - Nguyên nhân phổ biến: **{top_loi}**.
        - Khu vực nóng: **{vung_max}** có tỷ lệ thiết bị hỏng cao nhất.
        - Tình hình tài chính: Chi phí thực tế đang {'vượt' if cl > 0 else 'nằm trong'} ngân sách dự kiến.
        """
        st.info(ai_msg)
        st.write("---")
        st.write("💡 *Mẹo: Sếp có thể nhập thêm dữ liệu vào Sheets và nhấn Refresh để AI cập nhật nhận định mới.*")

    with t4:
        st.subheader("📁 Bảng đối soát Master")
        st.dataframe(df_final, use_container_width=True)

else:
    st.warning("Hệ thống đã kết nối nhưng chưa có dữ liệu hợp lệ để phân tích.")
