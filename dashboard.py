import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=1)
def load_data_v500_ultimate():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        cleaned_rows = []
        current_date = pd.to_datetime("2026-01-01")

        for i, row in df_raw.iterrows():
            # Đọc thô
            raw_ngay = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            ten_kh = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # --- THAY ĐỔI LỚN: BỘ LỌC ĐA TẦNG ---
            # 1. Bỏ qua dòng tiêu đề
            if i == 0 or "Mã số" in ma_may or "Mã máy" in ma_may:
                continue
            
            # 2. Bỏ qua dòng trống hoàn toàn (Chặn đứng lỗi 4000 ca)
            if not ma_may and not ten_kh:
                continue
            
            # 3. Kiểm tra tính hợp lệ của Mã máy (Phải có ít nhất 1 chữ cái hoặc số)
            if not re.search(r'[a-zA-Z0-9]', ma_may):
                continue

            # Xử lý ngày tháng
            parsed_date = pd.to_datetime(raw_ngay, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                current_date = parsed_date

            cleaned_rows.append({
                "NGÀY_DT": current_date,
                "NĂM": current_date.year,
                "THÁNG": current_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": ten_kh if ten_kh else "N/A",
                "LINH_KIỆN": linh_kien if linh_kien else "N/A",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung_mien else ("MIỀN TRUNG" if "TRUNG" in vung_mien else "MIỀN NAM")
            })
        
        final_df = pd.DataFrame(cleaned_rows)
        # Loại bỏ các dòng trùng lặp hoàn toàn nếu có
        return final_df.drop_duplicates()
    except:
        return pd.DataFrame()

# --- KHỞI CHẠY ---
df = load_data_v500_ultimate()

if not df.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V500")
        if st.button('🔄 LÀM SẠCH & ĐỒNG BỘ LẠI', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("Chọn Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    # --- GIAO DIỆN PRO V110 ---
    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")

    # KPI thực tế
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Tổng ca hỏng thực", len(df_final))
    with c2: st.metric("Số máy lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    with c3: 
        st.metric("Hỏng tái diễn", re_fail)
        if re_fail > 0: st.error("⚠️ Cần kiểm tra")
    with c4: st.metric("Số khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Tabs
    t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG", "🚩 RỦI RO", "🔍 TÌM KIẾM", "📁 DỮ LIỆU GỐC"])

    with t1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📈 Diễn biến hỏng hóc thực tế")
            # Group theo ngày để vẽ biểu đồ đường sạch
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True, 
                               title="Biểu đồ lỗi theo thời gian (Đã lọc rác)")
            fig_line.update_traces(line_color='#0047AB', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)
            
        with col2:
            st.subheader("📍 Phân bổ Vùng Miền")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.4, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        st.subheader("🚩 Thiết bị hỏng trên 1 lần")
        st.write(dup[dup > 1])

    with t3:
        search = st.text_input("Nhập Mã máy hoặc Tên KH để truy xuất:")
        if search:
            st.dataframe(df[df['MÃ_MÁY'].str.contains(search, case=False) | df['KHÁCH_HÀNG'].str.contains(search, case=False)])

    with t4:
        st.subheader("📁 Danh sách đã làm sạch (Chỉ còn dữ liệu thực)")
        st.dataframe(df_final, use_container_width=True)

else:
    st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Vui lòng kiểm tra lại file Google Sheets!")
