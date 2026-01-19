import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- THIẾT LẬP GIAO DIỆN CHUẨN PRO ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=1)
def load_data_v110_pro():
    try:
        # Đường dẫn dữ liệu từ Google Sheets của sếp
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_rows = []
        current_date = None 

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua hàng tiêu đề gốc
            
            ngay_txt = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            ten_kh = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- KHẮC PHỤC LỖI CHỖ TRỐNG & NGÀY THÁNG (CỐT LÕI) ---
            # Nếu không có Mã máy hoặc là dòng tiêu đề lặp lại -> Bỏ qua, không điền ngày xuống
            if not ma_may or "Mã số" in ma_may or len(ma_may) < 2:
                continue

            # Chỉ cập nhật ngày khi ô ngày thực sự có dữ liệu hợp lệ
            parsed_date = pd.to_datetime(ngay_txt, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                current_date = parsed_date
            
            # Nếu dòng có mã máy mà chưa có ngày (lỗi nhập dòng đầu), lấy mặc định 01/01/2026
            if current_date is None:
                current_date = pd.to_datetime("2026-01-01")

            valid_rows.append({
                "NGÀY_DT": current_date,
                "NĂM": current_date.year,
                "THÁNG": current_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": ten_kh,
                "LINH_KIỆN": linh_kien if linh_kien else "Chưa xác định",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung_raw else ("MIỀN TRUNG" if "TRUNG" in vung_raw else "MIỀN NAM")
            })
        return pd.DataFrame(valid_rows)
    except:
        return pd.DataFrame()

# --- KHỞI CHẠY HỆ THỐNG ---
df = load_data_v110_pro()

# Sidebar: Quản trị V110 (Đúng như hình image_f7eb45.png)
with st.sidebar:
    st.markdown("### 🛠️ QUẢN TRỊ V110")
    if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if not df.empty:
        st.divider()
        sel_year = st.selectbox("📅 Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Chọn Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

# --- HIỂN THỊ KPI (Đúng như hình image_f7dfc9) ---
if not df.empty:
    st.markdown("## 🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Tổng ca hỏng", len(df_final))
    with c2: st.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    # Tính toán Re-fail
    dup = df_final['MÃ_MÁY'].value_counts()
    refail_count = len(dup[dup > 1])
    with c3: 
        st.metric("Hỏng tái diễn (>1 lần)", refail_count)
        if refail_count > 0: st.write("🔴 **Cần chú trọng**")
        
    with c4: st.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

    # --- TABS CHỨC NĂNG (Đúng như hình image_f7d89c) ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 XU HƯỚNG & PHÂN BỐ", 
        "🚩 QUẢN TRỊ RỦI RO (RE-FAIL)", 
        "🔍 TRUY XUẤT NHANH", 
        "📁 DỮ LIỆU GỐC"
    ])

    with tab1:
        col_left, col_right = st.columns([1.6, 1])
        with col_left:
            st.subheader("📈 Xu hướng lỗi theo thời gian")
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)

        with col_right:
            st.subheader("📍 Phân bổ Vùng Miền")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                             color_discrete_map={'MIỀN BẮC':'#34D399', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#F87171'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("🔧 Phân tích Linh kiện lỗi")
        lk_chart = df_final['LINH_KIỆN'].value_counts().reset_index()
        fig_bar = px.bar(lk_chart, x='count', y='LINH_KIỆN', orientation='h', text='count')
        fig_bar.update_traces(marker_color='#1E3A8A')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with tab2:
        st.subheader("🚩 Danh sách thiết bị hỏng lặp lại")
        refail_df = dup[dup > 1].reset_index()
        refail_df.columns = ['Mã Máy', 'Số lần hỏng']
        st.table(refail_df.sort_values(by='Số lần hỏng', ascending=False))

    with tab3:
        st.subheader("🔍 Truy xuất nhanh")
        search = st.text_input("Nhập Mã Máy hoặc Khách Hàng:")
        if search:
            res = df[df['MÃ_MÁY'].str.contains(search, case=False) | df['KHÁCH_HÀNG'].str.contains(search, case=False)]
            st.dataframe(res, use_container_width=True)

    with tab4:
        st.subheader("📁 Dữ liệu chi tiết đã làm sạch")
        st.dataframe(df_final, use_container_width=True)
else:
    st.info("Hệ thống đã loại bỏ dữ liệu ảo. Vui lòng nhập dữ liệu thực vào Sheets.")
