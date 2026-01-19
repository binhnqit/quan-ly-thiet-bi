import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Báo Cáo Thực 2026", layout="wide")

@st.cache_data(ttl=1)
def load_data_v270():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        last_date = pd.to_datetime("2026-01-01") 
        
        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua tiêu đề
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung = str(row.iloc[5]).strip().upper()

            # --- BỘ LỌC "SẠCH 100%" ---
            # Chỉ lấy dòng nếu Mã Máy và Khách Hàng có dữ liệu thực sự (không tính dòng trống)
            if len(ma_may) < 2 or len(khach) < 2 or ma_may.lower() == "nan":
                continue 

            # Cập nhật ngày tiếp diễn
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse):
                last_date = dt_parse

            final_rows.append({
                "DATE_OBJ": last_date,
                "THÁNG": last_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": "BẮC" if "BẮC" in vung else ("TRUNG" if "TRUNG" in vung else "NAM")
            })
        return pd.DataFrame(final_rows)
    except:
        return pd.DataFrame()

data = load_data_v270()

if not data.empty:
    # Sidebar lọc
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V270")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU MỚI', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        sel_m = st.selectbox("Chọn Tháng:", sorted(data['THÁNG'].unique()))

    df_f = data[data['THÁNG'] == sel_m]

    # --- KPI CHÍNH ---
    st.title(f"📊 Báo cáo Tháng {sel_m}/2026 (Số thực)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng thật", f"{len(df_f)}")
    c2.metric("Số máy lỗi", df_f['MÃ_MÁY'].nunique())
    
    # Biểu đồ xu hướng (Sẽ không còn cột khổng lồ nữa)
    st.subheader("📈 Diễn biến hỏng hóc trong tháng")
    trend = df_f.groupby('DATE_OBJ').size().reset_index(name='Số ca')
    fig = px.bar(trend, x='DATE_OBJ', y='Số ca', text='Số ca')
    fig.update_traces(marker_color='#1E3A8A')
    st.plotly_chart(fig, use_container_width=True)
    
    # Bảng kiểm tra
    st.subheader("🔍 Danh sách đối soát thực tế")
    st.dataframe(df_f, use_container_width=True)
else:
    st.warning("Hệ thống đã lọc sạch dòng trống. Hiện chưa thấy dữ liệu thực nào. Sếp hãy nhập thêm vào Sheets nhé!")
