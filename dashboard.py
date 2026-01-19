import streamlit as st
import pandas as pd
import plotly.express as px
import time
import random

# 1. GIAO DIỆN CHUẨN EXECUTIVE
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi 2026", layout="wide")

@st.cache_data(ttl=2) # Giảm thời gian cache xuống tối thiểu
def load_data_v230():
    try:
        # Thêm random_token để ép Google Sheets cập nhật dữ liệu mới nhất sếp vừa nhập
        random_token = random.randint(1, 100000)
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&x={random_token}"
        
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        final_rows = []
        
        # Biến nhớ ngày gần nhất (Dùng cho logic điền ngày trống của sếp)
        last_valid_date = pd.to_datetime("2026-01-01") 

        for i, row in df_raw.iterrows():
            # Bỏ qua dòng tiêu đề (Dòng 1 trong Sheets)
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_str = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- ĐIỀU KIỆN TỐI ƯU: CHỈ LẤY DÒNG CÓ MÃ MÁY THỰC TẾ ---
            # Nếu cột Mã Máy trống hoặc quá ngắn (<3 ký tự), ta bỏ qua luôn để không tăng số ảo
            if len(ma_may) < 3 or ma_may.lower() == "nan":
                continue 

            # --- LOGIC ĐIỀN NGÀY TIẾP DIỄN ---
            temp_date = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
            if pd.notnull(temp_date):
                last_valid_date = temp_date # Cập nhật khi gặp ngày mới sếp nhập
            
            # Phân loại vùng miền chuẩn theo hình sếp gửi
            v_final = "KHÁC"
            if "BẮC" in vung_raw: v_final = "MIỀN BẮC"
            elif "TRUNG" in vung_raw: v_final = "MIỀN TRUNG"
            elif "NAM" in vung_raw: v_final = "MIỀN NAM"

            final_rows.append({
                "NGÀY": last_valid_date.strftime('%d/%m/%Y'),
                "DATE_KEY": last_valid_date,
                "THÁNG": last_valid_date.month,
                "NĂM": last_valid_date.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": v_final
            })

        return pd.DataFrame(final_rows)
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

# Nạp dữ liệu mới nhất
data = load_data_v230()

if not data.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ")
        if st.button('🔄 CẬP NHẬT LIVE DATA', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Lọc dữ liệu năm 2026
        df_2026 = data[data['NĂM'] == 2026]
        list_thang = ["Tất cả năm 2026"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Chọn kỳ báo cáo", list_thang)

    # Thực hiện lọc theo tháng sếp chọn
    if sel_m == "Tất cả năm 2026":
        df_filtered = df_2026
    else:
        m_num = int(sel_m.replace("Tháng ", ""))
        df_filtered = df_2026[df_2026['THÁNG'] == m_num]

    # --- HIỂN THỊ KPI (THEO HÌNH SẾP GỬI) ---
    st.title(f"📊 Báo cáo: {sel_m}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_filtered):,}")
    c2.metric("Số thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    
    re_counts = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn (>1)", len(re_counts[re_counts > 1]))
    c4.metric("Khách hàng báo lỗi", df_filtered['KHÁCH_HÀNG'].nunique())

    # --- BIỂU ĐỒ TỔNG QUAN ---
    col_l, col_r = st.columns([1.6, 1])
    with col_l:
        st.subheader("📈 Xu hướng hỏng hóc thực tế")
        # Gom nhóm theo ngày để vẽ biểu đồ đường
        trend = df_filtered.groupby('DATE_KEY').size().reset_index(name='Số ca')
        fig_line = px.line(trend.sort_values('DATE_KEY'), x='DATE_KEY', y='Số ca', markers=True)
        fig_line.update_traces(line_color='#1E3A8A', marker=dict(size=10))
        st.plotly_chart(fig_line, use_container_width=True)
                
    with col_r:
        st.subheader("📍 Tỷ lệ Vùng Miền")
        fig_pie = px.pie(df_filtered, names='VÙNG', hole=0.6, 
                         color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#EF4444'})
        st.plotly_chart(fig_pie, use_container_width=True)
        
    # --- BẢNG TRA CỨU ---
    st.subheader("📋 Danh sách đối soát (Đã điền ngày tự động)")
    st.dataframe(df_filtered[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
else:
    st.info("Sếp vui lòng kiểm tra lại file Google Sheets. Hệ thống hiện không tìm thấy dữ liệu hợp lệ cho năm 2026.")
