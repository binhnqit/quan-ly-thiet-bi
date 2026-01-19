import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ Thống Phân Tích Thực 2026", layout="wide")

@st.cache_data(ttl=1)
def load_data_v280():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        last_date = pd.to_datetime("2026-01-01") 

        for i, row in df_raw.iterrows():
            if i == 0: continue
            
            # Đọc dữ liệu thô
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            vung = str(row.iloc[5]).strip().upper()

            # --- BỘ LỌC CHUYÊN GIA: CHẶN ĐỨNG DỮ LIỆU CỘNG DỒN ---
            # Chỉ chấp nhận dòng nếu Mã máy có dữ liệu thực sự (Không phải "Mã số máy" tiêu đề, không phải trống)
            if ma_may == "" or "Mã số" in ma_may or len(ma_may) < 2:
                continue

            # Xử lý ngày: Nếu có ngày mới thì cập nhật, không thì giữ ngày cũ
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse):
                last_date = dt_parse

            final_rows.append({
                "DATE_OBJ": last_date,
                "THÁNG": last_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": str(row.iloc[3]).strip(),
                "VÙNG": "BẮC" if "BẮC" in vung else ("TRUNG" if "TRUNG" in vung else "NAM")
            })
        
        return pd.DataFrame(final_rows)
    except:
        return pd.DataFrame()

data = load_data_v280()

if not data.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ CHUẨN")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU THỰC', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Chỉ lọc những tháng THỰC SỰ có dữ liệu
        list_thang = sorted(data['THÁNG'].unique())
        sel_m = st.selectbox("Chọn Tháng:", list_thang)

    df_f = data[data['THÁNG'] == sel_m]

    # --- HIỂN THỊ KPI THỰC ---
    st.title(f"📊 Báo cáo Tháng {sel_m}/2026")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng thật", len(df_f))
    c2.metric("Số máy lỗi", df_f['MÃ_MÁY'].nunique())
    
    # Biểu đồ xu hướng (Dạng cột để thấy sự tách biệt ngày)
    st.subheader("📈 Diễn biến hỏng hóc thực tế theo ngày")
    trend = df_f.groupby('DATE_OBJ').size().reset_index(name='Số ca')
    fig = px.bar(trend, x='DATE_OBJ', y='Số ca', text='Số ca')
    fig.update_traces(marker_color='#1E3A8A', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    # Danh sách đối soát (Để sếp thấy không còn dòng rác)
    st.subheader("🔍 Danh sách chi tiết")
    st.dataframe(df_f, use_container_width=True)
else:
    st.error("⚠️ Hệ thống đã loại bỏ toàn bộ dữ liệu ảo. Hiện tại không tìm thấy dòng dữ liệu thực nào trong Sheets.")
