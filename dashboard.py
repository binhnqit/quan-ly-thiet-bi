import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CẤU HÌNH GIAO DIỆN CHUẨN PRO ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi - PRO", layout="wide")

# Hàm làm sạch dữ liệu đầu vào (Core Engine)
@st.cache_data(ttl=1)
def get_clean_data_pro():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_data = []
        last_date = pd.to_datetime("2026-01-01")

        for i, row in df.iterrows():
            if i == 0: continue # Bỏ qua header
            
            # Đọc các cột quan trọng
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # BỘ LỌC CHUYÊN GIA: Chỉ lấy dòng có nội dung thực sự
            if not ma_may or "Mã số" in ma_may or len(ma_may) < 2: continue
            if not khach or "Tên KH" in khach: continue

            # Xử lý ngày tháng
            dt = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt): last_date = dt

            valid_data.append({
                "NGÀY_DT": last_date,
                "NĂM": last_date.year,
                "THÁNG": last_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": linh_kien if linh_kien else "Không xác định",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung_raw else ("MIỀN TRUNG" if "TRUNG" in vung_raw else "MIỀN NAM")
            })
        return pd.DataFrame(valid_data)
    except:
        return pd.DataFrame()

# --- 1. SIDEBAR: QUẢN TRỊ VÀ BỘ LỌC ---
df = get_clean_data_pro()

with st.sidebar:
    st.markdown("### 📍 QUẢN TRỊ V310")
    if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    if not df.empty:
        selected_year = st.selectbox("📅 Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_year = df[df['NĂM'] == selected_year]
        
        months = ["Tất cả"] + sorted(df_year['THÁNG'].unique().tolist())
        selected_month = st.selectbox("🗓️ Chọn Tháng", months)
        
        df_final = df_year if selected_month == "Tất cả" else df_year[df_year['THÁNG'] == selected_month]
    else:
        st.error("Chưa có dữ liệu sạch.")
        st.stop()

# --- 2. HEADER & KPI (NHƯ HÌNH V110) ---
st.title("📊 Hệ Thống Phân Tích Lỗi Thiết Bị")

c1, c2, c3, c4 = st.columns(4)
total_fails = len(df_final)
unique_machines = df_final['MÃ_MÁY'].nunique()
unique_customers = df_final['KHÁCH_HÀNG'].nunique()

# Tính hỏng tái diễn (Re-fail)
refail_counts = df_final['MÃ_MÁY'].value_counts()
refail_units = len(refail_counts[refail_counts > 1])

with c1: st.metric("Tổng ca hỏng", total_fails)
with c2: st.metric("Thiết bị lỗi", unique_machines)
with c3: 
    st.metric("Hỏng tái diễn (>1 lần)", refail_units)
    if refail_units > 0: st.caption("🔴 Cần chú trọng")
with c4: st.metric("Khách hàng báo lỗi", unique_customers)

# --- 3. TABS CHỨC NĂNG CHUYÊN NGHIỆP ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 XU HƯỚNG & PHÂN BỐ", 
    "🚩 QUẢN TRỊ RỦI RO (RE-FAIL)", 
    "🔍 TRUY XUẤT NHANH", 
    "📁 DỮ LIỆU GỐC"
])

with tab1:
    col_chart1, col_chart2 = st.columns([1.6, 1])
    
    with col_chart1:
        st.subheader("📈 Xu hướng lỗi theo thời gian")
        trend_df = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
        fig_line = px.line(trend_df, x='NGÀY_DT', y='Số ca', markers=True)
        fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy')
        fig_line.update_layout(hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col_chart2:
        st.subheader("📍 Phân bổ Vùng Miền")
        fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                         color_discrete_map={'MIỀN BẮC':'#34D399', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#F87171'})
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    st.subheader("🔧 Phân tích Linh kiện lỗi")
    lk_df = df_final['LINH_KIỆN'].value_counts().reset_index()
    fig_bar = px.bar(lk_df, x='count', y='LINH_KIỆN', orientation='h', text='count')
    fig_bar.update_traces(marker_color='#1E3A8A')
    st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.subheader("🚩 Danh sách thiết bị hỏng tái diễn")
    bad_machines = refail_counts[refail_counts > 1].reset_index()
    bad_machines.columns = ['Mã Máy', 'Số lần hỏng']
    st.table(bad_machines.sort_values(by='Số lần hỏng', ascending=False))

with tab3:
    st.subheader("🔍 Tìm kiếm lịch sử thiết bị")
    search_id = st.text_input("Nhập Mã Máy hoặc Tên Khách Hàng để truy xuất nhanh:")
    if search_id:
        result = df[df['MÃ_MÁY'].str.contains(search_id, case=False) | df['KHÁCH_HÀNG'].str.contains(search_id, case=False)]
        st.dataframe(result[['NGÀY_DT', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)

with tab4:
    st.subheader("📁 Toàn bộ dữ liệu sạch")
    st.dataframe(df_final, use_container_width=True)
