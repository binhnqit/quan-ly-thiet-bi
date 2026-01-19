import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH GIAO DIỆN CHUẨN PRO V110 ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=1)
def load_data_pro_v330():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_rows = []
        current_date = None # Khởi tạo ngày trống

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua tiêu đề gốc
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            vung = str(row.iloc[5]).strip().upper()

            # --- KHẮC PHỤC LỖI NGÀY THÁNG & SỐ ẢO ---
            # Bước 1: Nếu dòng hoàn toàn không có Mã máy hoặc là tiêu đề lặp lại -> BỎ QUA NGAY
            if not ma_may or "Mã số" in ma_may or len(ma_may) < 2:
                continue

            # Bước 2: Chỉ cập nhật ngày nếu ô Ngày có dữ liệu mới
            parsed_date = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                current_date = parsed_date
            
            # Bước 3: Nếu vẫn chưa có ngày (dòng đầu tiên lỗi ngày) -> lấy mặc định 01/01/2026
            if current_date is None:
                current_date = pd.to_datetime("2026-01-01")

            valid_rows.append({
                "NGÀY_DT": current_date,
                "NĂM": current_date.year,
                "THÁNG": current_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": str(row.iloc[3]).strip(),
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung else ("MIỀN TRUNG" if "TRUNG" in vung else "MIỀN NAM")
            })
        
        return pd.DataFrame(valid_rows)
    except:
        return pd.DataFrame()

# --- GIAO DIỆN CHỨC NĂNG CHÍNH ---
df = load_data_pro_v330()

with st.sidebar:
    st.markdown("### 🛠️ QUẢN TRỊ V110")
    if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if not df.empty:
        st.divider()
        sel_year = st.selectbox("📅 Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_year = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Chọn Tháng", ["Tất cả"] + sorted(df_year['THÁNG'].unique().tolist()))
        
        df_final = df_year if sel_month == "Tất cả" else df_year[df_year['THÁNG'] == sel_month]
    else:
        st.stop()

# --- HEADER KPI (Đúng như hình image_f7dfc9) ---
st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Tổng ca hỏng", len(df_final))
with c2: st.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())

# Tính hỏng tái diễn
dup = df_final['MÃ_MÁY'].value_counts()
refail_count = len(dup[dup > 1])
with c3: 
    st.metric("Hỏng tái diễn (>1 lần)", refail_count)
    if refail_count > 0: st.markdown("🔴 **Cần chú trọng**")

with c4: st.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

# --- TABS CHỨC NĂNG (Đúng như hình image_f7d89c) ---
t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG & PHÂN BỐ", "🚩 QUẢN TRỊ RỦI RO (RE-FAIL)", "🔍 TRUY XUẤT NHANH", "📁 DỮ LIỆU GỐC"])

with t1:
    col_l, col_r = st.columns([1.6, 1])
    with col_l:
        st.subheader("📈 Xu hướng lỗi theo thời gian")
        trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
        fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
        fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy')
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col_r:
        st.subheader("📍 Phân bổ Vùng Miền")
        fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                         color_discrete_map={'MIỀN BẮC':'#34D399', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#F87171'})
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    st.subheader("🔧 Phân tích Linh kiện lỗi")
    lk_data = df_final['LINH_KIỆN'].value_counts().reset_index()
    fig_bar = px.bar(lk_data, x='count', y='LINH_KIỆN', orientation='h', text='count')
    fig_bar.update_traces(marker_color='#1E3A8A')
    st.plotly_chart(fig_bar, use_container_width=True)

with t2:
    st.subheader("🚩 Danh sách thiết bị cần chú ý (Hỏng nhiều lần)")
    bad_list = dup[dup > 1].reset_index()
    bad_list.columns = ['Mã Máy', 'Số lần hỏng']
    st.dataframe(bad_list, use_container_width=True)

with t3:
    st.subheader("🔍 Truy xuất nhanh")
    search = st.text_input("Nhập Mã Máy hoặc Tên Khách Hàng để tìm kiếm:")
    if search:
        search_res = df[df['MÃ_MÁY'].str.contains(search, case=False) | df['KHÁCH_HÀNG'].str.contains(search, case=False)]
        st.dataframe(search_res, use_container_width=True)

with t4:
    st.subheader("📋 Dữ liệu sạch đối soát")
    st.dataframe(df_final, use_container_width=True)
