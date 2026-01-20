import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Hệ Thống Sức Khỏe Thiết Bị V11", layout="wide")

@st.cache_data(ttl=2)
def load_data_health():
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
                cp_tt = pd.to_numeric(str(row.iloc[8]).replace(',', ''), errors='coerce') or 0
                clean_data.append({
                    "NGÀY": p_date, "NĂM": p_date.year, "THÁNG": p_date.month,
                    "MÃ_MÁY": ma_may, "KHÁCH_HÀNG": str(row.iloc[2]).strip(),
                    "LINH_KIỆN": str(row.iloc[3]).strip(), "VÙNG": str(row.iloc[5]).strip(),
                    "CP_THUC_TE": cp_tt
                })
        return pd.DataFrame(clean_data)
    except: return pd.DataFrame()

df = load_data_health()

if not df.empty:
    with st.sidebar:
        st.title("🛡️ ASSET HEALTH")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU'):
            st.cache_data.clear()
            st.rerun()
        # Lọc đa năm để so sánh
        all_years = sorted(df['NĂM'].unique())
        selected_years = st.multiselect("📅 Chọn năm so sánh", all_years, default=all_years)
        df_filtered = df[df['NĂM'].isin(selected_years)]

    st.markdown("## 📊 ĐÁNH GIÁ TÌNH TRẠNG SỨC KHỎE LAPTOP")

    t1, t2, t3 = st.tabs(["📉 SO SÁNH NĂM", "🩺 TÌNH TRẠNG MÁY (THANH LÝ)", "🤖 AI TƯ VẤN"])

    with t1:
        st.subheader("So sánh lượng máy hư qua các năm")
        yearly_compare = df.groupby('NĂM').size().reset_index(name='Số ca hỏng')
        fig_year = px.bar(yearly_compare, x='NĂM', y='Số ca hỏng', text_auto=True,
                          color='NĂM', title="Tổng hợp hỏng hóc đa năm")
        st.plotly_chart(fig_year, use_container_width=True)

    with t2:
        st.subheader("📋 Danh sách máy xuống cấp (Cần ưu tiên thanh lý)")
        # Gom nhóm theo mã máy để tính toán sức khỏe
        health_report = df.groupby('MÃ_MÁY').agg({
            'NGÀY': 'count',
            'CP_THUC_TE': 'sum',
            'LINH_KIỆN': lambda x: ', '.join(x.unique())
        }).rename(columns={'NGÀY': 'Số lần hỏng', 'CP_THUC_TE': 'Tổng chi phí sửa'})
        
        # Đưa ra đánh giá
        def evaluate_health(row):
            if row['Số lần hỏng'] >= 4: return "🔴 THANH LÝ NGAY"
            if row['Số lần hỏng'] == 3: return "🟡 THEO DÕI CHẶT"
            return "🟢 CÒN TỐT"
            
        health_report['ĐÁNH GIÁ'] = health_report.apply(evaluate_health, axis=1)
        st.dataframe(health_report.sort_values('Số lần hỏng', ascending=False), use_container_width=True)

    with t3:
        st.subheader("🤖 Trợ lý AI - Đánh giá chuyên sâu")
        bad_machines = health_report[health_report['Số lần hỏng'] >= 3]
        total_expense = df['CP_THUC_TE'].sum()
        
        ai_advice = f"""
        **Phân tích của chuyên gia:**
        1. **Xu hướng xuống cấp:** Lượng hỏng hóc năm {max(all_years)} {'tăng' if len(df[df['NĂM']==max(all_years)]) > len(df[df['NĂM']==min(all_years)]) else 'giảm'} so với năm {min(all_years)}.
        2. **Danh sách đen:** Có **{len(bad_machines)}** máy đã hỏng trên 3 lần. Đây là những máy "ngốn" ngân sách nhất.
        3. **Gợi ý thanh lý:** Sếp nên ưu tiên thanh lý các máy có đánh giá 🔴 vì chi phí vận hành đang cao hơn giá trị sử dụng.
        4. **Linh kiện hay lỗi:** Chủ yếu hỏng **{df['LINH_KIỆN'].value_counts().idxmax()}**, sếp nên kiểm tra lại điều kiện môi trường sử dụng (nhiệt độ, độ ẩm).
        """
        st.info(ai_advice)

else:
    st.warning("Hệ thống đang chờ dữ liệu để phân tích sức khỏe.")
