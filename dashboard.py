import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- 1. THIẾT LẬP GIAO DIỆN CHUẨN PRO (Theo hình image_f7d89c) ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=1)
def load_data_v110_ultimate():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_rows = []
        current_date = None 

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua header gốc của Sheets
            
            # Đọc dữ liệu thô
            raw_ngay = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            ten_kh = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- KHẮC PHỤC LỖI CHỖ TRỐNG (THEO CHỈ ĐẠO CỦA SẾP) ---
            # Chỉ xử lý nếu dòng có Mã máy thực sự. Chặn đứng các dòng "Mã số máy", "Tên KH" hoặc dòng trống.
            if not ma_may or "Mã số" in ma_may or "Tên KH" in ten_kh or len(ma_may) < 2:
                continue

            # Cập nhật ngày tháng: Chỉ cập nhật khi ô ngày có giá trị hợp lệ
            parsed_date = pd.to_datetime(raw_ngay, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                current_date = parsed_date
            
            # Nếu dòng có mã máy mà chưa xác định được ngày (dòng đầu tiên rỗng ngày), mặc định 01/01/2026
            if current_date is None:
                current_date = pd.to_datetime("2026-01-01")

            valid_rows.append({
                "NGÀY_DT": current_date,
                "NĂM": current_date.year,
                "THÁNG": current_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": ten_kh,
                "LINH_KIỆN": linh_kien if linh_kien else "N/A",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung_raw else ("MIỀN TRUNG" if "TRUNG" in vung_raw else "MIỀN NAM")
            })
        
        return pd.DataFrame(valid_rows)
    except Exception as e:
        return pd.DataFrame()

# --- 2. GIAO DIỆN QUẢN TRỊ (Sidebar Chuẩn PRO) ---
df = load_data_v110_ultimate()

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
        
        # Lọc dữ liệu theo kỳ báo cáo
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

# --- 3. HIỂN THỊ CHỨC NĂNG (Đúng như hình image_f7d89c) ---
if not df.empty:
    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")

    # KPI Row (Chuẩn mẫu V110)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Tổng ca hỏng", len(df_final))
    with c2: st.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    # Tính hỏng tái diễn
    dup = df_final['MÃ_MÁY'].value_counts()
    refail = len(dup[dup > 1])
    with c3: 
        st.metric("Hỏng tái diễn (>1 lần)", refail)
        if refail > 0: st.markdown("🔴 **Cần chú trọng**")
        
    with c4: st.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

    # Các Tab chức năng (Đúng thứ tự sếp yêu cầu)
    t1, t2, t3, t4 = st.tabs([
        "📊 XU HƯỚNG & PHÂN BỐ", 
        "🚩 QUẢN TRỊ RỦI RO (RE-FAIL)", 
        "🔍 TRUY XUẤT NHANH", 
        "📁 DỮ LIỆU GỐC"
    ])

    with t1:
        # Layout Xu hướng & Vùng miền
        col_l, col_r = st.columns([1.6, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi theo thời gian")
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy') # Màu xanh chuyên nghiệp, có đổ bóng
            st.plotly_chart(fig_line, use_container_width=True)

        with col_r:
            st.subheader("📍 Phân bổ Vùng Miền")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                             color_discrete_map={'MIỀN BẮC':'#34D399', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#F87171'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        # Phân tích linh kiện (Hình image_f7d89c dưới cùng)
        st.subheader("🔧 Phân tích Linh kiện lỗi")
        lk_count = df_final['LINH_KIỆN'].value_counts().reset_index()
        fig_bar = px.bar(lk_count, x='count', y='LINH_KIỆN', orientation='h', text='count')
        fig_bar.update_traces(marker_color='#1E3A8A')
        st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.subheader("🚩 Danh sách thiết bị hỏng tái diễn")
        bad_df = dup[dup > 1].reset_index()
        bad_df.columns = ['Mã Máy', 'Số lần hỏng']
        st.table(bad_df.sort_values(by='Số lần hỏng', ascending=False))

    with t3:
        st.subheader("🔍 Tìm kiếm nhanh")
        query = st.text_input("Gõ Mã Máy hoặc Tên Khách Hàng để truy xuất lịch sử:")
        if query:
            res = df[df['MÃ_MÁY'].str.contains(query, case=False) | df['KHÁCH_HÀNG'].str.contains(query, case=False)]
            st.dataframe(res[['NGÀY_DT', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)

    with t4:
        st.subheader("📋 Dữ liệu thực tế đã đối soát")
        st.dataframe(df_final, use_container_width=True)

else:
    st.warning("Hệ thống đã loại bỏ 100% dòng trống và tiêu đề rác. Sếp hãy kiểm tra lại dữ liệu đầu vào!")
