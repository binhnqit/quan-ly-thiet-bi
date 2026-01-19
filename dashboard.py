import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi V1300", layout="wide")

@st.cache_data(ttl=0) # Vô hiệu hóa hoàn toàn cache để debug
def load_data_ultra_clean():
    try:
        # ÉP GOOGLE SHEETS CẬP NHẬT BẰNG CÁCH THÊM BIẾN TIME VÀO URL
        timestamp = int(time.time())
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&gid=0&single=true&cachebuster={timestamp}"
        
        # Đọc dữ liệu
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        processed_data = []
        current_date = None
        rows_dropped = 0

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua tiêu đề
            
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach_hang = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # 1. CẬP NHẬT NGÀY THÁNG
            temp_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            if pd.notnull(temp_date):
                current_date = temp_date

            # 2. BỘ LỌC TỐI THƯỢNG (BỨC PHÁ Ở ĐÂY)
            # Một dòng CHỈ ĐƯỢC CHẤP NHẬN nếu Mã Máy có ít nhất 2 ký tự chữ/số
            # Điều này loại bỏ 100% các dòng trống có định dạng ẩn ở cuối Sheets
            if not ma_may or len(ma_may) < 2 or "Mã số" in ma_may:
                rows_dropped += 1
                continue
            
            # 3. GÁN DỮ LIỆU VÀO DANH SÁCH SẠCH
            if current_date:
                processed_data.append({
                    "NGÀY": current_date,
                    "NĂM": current_date.year,
                    "THÁNG": current_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": khach_hang if khach_hang else "N/A",
                    "LINH_KIỆN": linh_kien if linh_kien else "Chưa rõ",
                    "VÙNG": "BẮC" if "BẮC" in vung_mien else ("TRUNG" if "TRUNG" in vung_mien else "NAM")
                })
        
        return pd.DataFrame(processed_data), rows_dropped, len(df_raw)
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame(), 0, 0

# --- THI ĐẶT DỮ LIỆU ---
df, dropped, total_raw = load_data_ultra_clean()

if not df.empty:
    with st.sidebar:
        st.header("⚙️ CONTROL PANEL V1300")
        if st.button('🔄 FORCE REFRESH (ÉP CẬP NHẬT)', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("📅 Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    # --- GIAO DIỆN CHÍNH ---
    st.title("🛡️ Hệ Thống Giám Sát Thiết Bị - Số Liệu Thực")
    
    # KPI - Số liệu thực tế sau khi đã lọc rác
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Số máy lỗi", df_final['MÃ_MÁY'].nunique())
    
    counts = df_final['MÃ_MÁY'].value_counts()
    refail = len(counts[counts > 1])
    c3.metric("Hỏng tái diễn", refail, delta_color="inverse")
    c4.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Tabs
    t1, t2, t3 = st.tabs(["📊 BIỂU ĐỒ XU HƯỚNG", "🚩 CẢNH BÁO RE-FAIL", "🔍 DEBUG DỮ LIỆU"])

    with t1:
        st.subheader("📈 Diễn biến hỏng hóc (Dữ liệu đã làm sạch)")
        trend = df_final.groupby('NGÀY').size().reset_index(name='Số ca')
        # Biểu đồ đường của Apple Style: Sạch, rõ ràng, không có cột ảo
        fig = px.line(trend, x='NGÀY', y='Số ca', markers=True, text='Số ca')
        fig.update_traces(line_color='#007AFF', fill='tozeroy', textposition="top center")
        st.plotly_chart(fig, use_container_width=True)
        

    with t2:
        st.subheader("🚩 Danh sách máy hỏng trên 1 lần")
        if refail > 0:
            st.table(counts[counts > 1])
        else:
            st.success("Tuyệt vời! Không có máy nào hỏng tái diễn.")

    with t3:
        st.subheader("📁 Nhật ký lọc dữ liệu (Dành cho sếp kiểm tra)")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Tổng dòng đọc được từ Sheets", total_raw)
        col_b.metric("Số dòng rác đã loại bỏ", dropped)
        col_c.metric("Số dòng dữ liệu thật", len(df))
        
        st.write("Dữ liệu sau khi xử lý:")
        st.dataframe(df_final, use_container_width=True)

else:
    st.error("Hệ thống không tìm thấy dữ liệu hợp lệ. Sếp hãy chắc chắn đã nhập 'Mã số máy' vào Sheets.")
    if st.button("Thử lại"): st.rerun()
