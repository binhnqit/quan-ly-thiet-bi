import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH GIAO DIỆN CHUẨN V110 ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi - V900", layout="wide")

@st.cache_data(ttl=0) # Ép bộ nhớ đệm về 0 để dữ liệu luôn mới nhất
def load_data_v900_perfect():
    try:
        # Giữ nguyên kết nối Google Sheets trơn tru của sếp
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_records = []
        last_valid_date = None 

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua dòng tiêu đề
            
            # Đọc dữ liệu thô từ các cột
            raw_ngay = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach_hang = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # --- GIẢI PHÁP BỨC PHÁ: CHỈ LẤY DÒNG CÓ MÃ MÁY THỰC ---
            # Nếu dòng không có mã máy -> Đây là dòng trống hoặc rác ở cuối Sheets -> BỎ QUA
            if not ma_may or "Mã số" in ma_may or len(ma_may) < 2:
                continue

            # --- XỬ LÝ NGÀY THÁNG CHUẨN ---
            current_date_parsed = pd.to_datetime(raw_ngay, dayfirst=True, errors='coerce')
            
            if pd.notnull(current_date_parsed):
                # Nếu dòng này có ngày mới, cập nhật mốc thời gian
                last_valid_date = current_date_parsed
            
            # Chỉ ghi nhận record nếu đã có ít nhất 1 mốc ngày tháng hợp lệ
            if last_valid_date:
                valid_records.append({
                    "NGÀY_DT": last_valid_date,
                    "NĂM": last_valid_date.year,
                    "THÁNG": last_valid_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": khach_hang if khach_hang else "Chưa xác định",
                    "LINH_KIỆN": linh_kien if linh_kien else "N/A",
                    "VÙNG": "MIỀN BẮC" if "BẮC" in vung_mien else ("MIỀN TRUNG" if "TRUNG" in vung_mien else "MIỀN NAM")
                })
        
        return pd.DataFrame(valid_records)
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu: {e}")
        return pd.DataFrame()

# --- XỬ LÝ DỮ LIỆU ---
df = load_data_v900_perfect()

if not df.empty:
    with st.sidebar:
        st.markdown("### ⚙️ QUẢN TRỊ HỆ THỐNG")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU SẠCH', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        list_year = sorted(df['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_year)
        
        df_year = df[df['NĂM'] == sel_year]
        list_month = ["Tất cả"] + sorted(df_year['THÁNG'].unique().tolist())
        sel_month = st.selectbox("🗓️ Chọn Tháng", list_month)
        
        df_final = df_year if sel_month == "Tất cả" else df_year[df_year['THÁNG'] == sel_month]

    # --- HIỂN THỊ KPI (THEO ĐÚNG GIAO DIỆN ĐẸP CỦA SẾP) ---
    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng THỰC", len(df_final))
    c2.metric("Số máy lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    c3.metric("Hỏng tái diễn", re_fail)
    c4.metric("Số khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG & VÙNG MIỀN", "🚩 RỦI RO (RE-FAIL)", "🔍 TRUY XUẤT", "📁 DỮ LIỆU GỐC SẠCH"])

    with t1:
        col_l, col_r = st.columns([1.6, 1])
        with col_l:
            st.subheader("📈 Diễn biến hỏng hóc thực tế")
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#0047AB', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)

        with col_r:
            st.subheader("📍 Phân bổ theo Vùng")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        st.subheader("🚩 Danh sách thiết bị báo động (Hỏng > 1 lần)")
        if re_fail > 0:
            st.write(dup[dup > 1])
        else:
            st.success("Không có máy hỏng lặp lại.")

    with t3:
        query = st.text_input("🔍 Tìm nhanh Mã máy hoặc Khách hàng:")
        if query:
            search_df = df[df['MÃ_MÁY'].str.contains(query, case=False) | df['KHÁCH_HÀNG'].str.contains(query, case=False)]
            st.dataframe(search_df, use_container_width=True)

    with t4:
        st.subheader("📁 Đối soát dữ liệu đã lọc rác")
        st.dataframe(df_final, use_container_width=True)

else:
    st.info("Hệ thống đã loại bỏ hoàn toàn dòng ảo. Đang chờ dữ liệu thực từ Google Sheets.")
