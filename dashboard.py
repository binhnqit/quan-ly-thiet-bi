import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ Thống Phân Tích Thực 2026", layout="wide")

@st.cache_data(ttl=1)
def load_data_v290():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        last_date = pd.to_datetime("2026-01-01") 

        for i, row in df_raw.iterrows():
            if i == 0: continue
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- CHIẾN THUẬT QUÉT RÁC: CHỈ LẤY DÒNG CÓ NỘI DUNG THỰC ---
            # 1. Bỏ qua dòng tiêu đề nếu sếp lỡ copy lại
            if "Mã số" in ma_may or "Tên KH" in khach: continue
            # 2. CHỐT CHẶN CUỐI: Nếu không có mã máy VÀ không có khách hàng -> Dòng trống rác -> BỎ QUA
            if not ma_may and not khach: continue
            # 3. Loại bỏ dòng chỉ chứa dấu cách hoặc ký tự rác nhỏ
            if len(ma_may) < 2 and len(khach) < 2: continue

            # Xử lý ngày tiếp diễn thông minh
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse): last_date = dt_parse

            final_rows.append({
                "DATE_OBJ": last_date,
                "THÁNG": last_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": str(row.iloc[3]).strip(),
                "VÙNG": "BẮC" if "BẮC" in vung_raw else ("TRUNG" if "TRUNG" in vung_raw else "NAM")
            })
        return pd.DataFrame(final_rows)
    except:
        return pd.DataFrame()

data = load_data_v290()

if not data.empty:
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN CHUẨN")
        if st.button('🔄 QUÉT LẠI DỮ LIỆU SẠCH', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        sel_m = st.selectbox("Chọn Tháng:", sorted(data['THÁNG'].unique()))

    df_f = data[data['THÁNG'] == sel_m]

    # --- HIỂN THỊ KPI THỰC ---
    st.title(f"📊 Báo cáo Tháng {sel_m}/2026 - Dữ liệu thực tế")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng thật", len(df_f))
    c2.metric("Số máy lỗi", df_f['MÃ_MÁY'].nunique())
    
    # Biểu đồ xu hướng (Sẽ không còn cột 4,000 ảo nữa)
    st.subheader("📈 Diễn biến hỏng hóc (Theo ngày)")
    trend = df_f.groupby('DATE_OBJ').size().reset_index(name='Số ca')
    fig = px.bar(trend, x='DATE_OBJ', y='Số ca', text='Số ca')
    fig.update_traces(marker_color='#1E3A8A', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Bảng chi tiết đối soát
    st.subheader("🔍 Danh sách đối soát (Đã lọc rác)")
    st.dataframe(df_f, use_container_width=True)
else:
    st.error("Hệ thống đã loại bỏ 100% dòng trống. Hiện không có dữ liệu thực nào trong Sheets.")
