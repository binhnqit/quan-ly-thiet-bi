import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

# Hàm làm sạch dữ liệu cốt lõi
@st.cache_data(ttl=2)
def load_expert_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    try:
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        data, memo = [], {"date": None, "customer": "N/A", "region": "N/A"}

        for i, row in df_raw.iterrows():
            if i == 0: continue
            
            # Đọc dữ liệu thô
            r_date, r_may, r_kh, r_lk, r_vung = [str(row.iloc[j]).strip() for j in [0, 1, 2, 3, 5]]
            
            # Logic Healing: Điền trống thông minh
            p_date = pd.to_datetime(r_date, dayfirst=True, errors='coerce')
            if pd.notnull(p_date): memo["date"] = p_date
            if r_kh: memo["customer"] = r_kh
            if r_vung: memo["region"] = r_vung

            # BỘ LỌC CHUYÊN GIA: Chỉ lấy dòng có Mã máy thực sự & Ngày hợp lệ
            if r_may and len(r_may) > 1 and memo["date"]:
                # Chỉ lấy dữ liệu từ 2024 đến nay để tránh rác năm 2200
                if 2024 <= memo["date"].year <= 2026:
                    data.append({
                        "NGÀY_DT": memo["date"], "NĂM": memo["date"].year, "THÁNG": memo["date"].month,
                        "MÃ_MÁY": r_may, "KHÁCH_HÀNG": memo["customer"],
                        "LINH_KIỆN": r_lk if r_lk else "Chưa xác định",
                        "VÙNG": "MIỀN NAM" if "NAM" in memo["region"].upper() else 
                                ("MIỀN BẮC" if "BẮC" in memo["region"].upper() else "MIỀN TRUNG")
                    })
        return pd.DataFrame(data)
    except: return pd.DataFrame()

# --- XỬ LÝ GIAO DIỆN ---
df = load_expert_data()

# SIDEBAR: QUẢN TRỊ V110
with st.sidebar:
    st.markdown("### ⚙️ QUẢN TRỊ V110")
    if st.button("🔄 ĐỒNG BỘ DỮ LIỆU", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if not df.empty:
        sel_year = st.selectbox("📅 Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Chọn Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]
    else:
        df_final = pd.DataFrame()

# NỘI DUNG CHÍNH
st.title("📊 Hệ Thống Phân Tích Lỗi Thiết Bị")

if not df_final.empty:
    # 1. HÀNG KPI (Như hình sếp gửi)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    re_fail = df_final['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn (>1)", len(re_fail[re_fail > 1]))
    c4.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

    # 2. KHU VỰC BIỂU ĐỒ (Tab Layout)
    t1, t2, t3 = st.tabs(["📈 XU HƯỚNG & PHÂN BỔ", "🚩 QUẢN TRỊ RỦI RO", "📁 DỮ LIỆU GỐC"])
    
    with t1:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("📌 Xu hướng lỗi theo thời gian")
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True, line_shape="spline")
            fig_line.update_traces(line_color='#1f77b4', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)
        
        with col_right:
            st.subheader("📍 Phân bổ Vùng Miền")
            vung_data = df_final['VÙNG'].value_counts().reset_index()
            fig_pie = px.pie(vung_data, values='count', names='VÙNG', hole=0.5,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("🔧 Phân tích Linh kiện lỗi")
        lk_data = df_final['LINH_KIỆN'].value_counts().reset_index().head(10)
        fig_bar = px.bar(lk_data, x='count', y='LINH_KIỆN', orientation='h', text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.subheader("🚩 Danh sách thiết bị hỏng tái diễn")
        if not re_fail[re_fail > 1].empty:
            st.dataframe(re_fail[re_fail > 1], use_container_width=True)
        else:
            st.success("Chưa phát hiện thiết bị nào hỏng tái diễn trong kỳ này.")

    with t3:
        st.subheader("📁 Đối soát dữ liệu sạch")
        st.dataframe(df_final, use_container_width=True)
else:
    st.info("👋 Chào sếp! Hệ thống đã sẵn sàng. Hãy nhập dữ liệu vào Google Sheets để bắt đầu phân tích.")
