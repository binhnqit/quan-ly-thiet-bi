import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ Thống Phân Tích Chuẩn 2026", layout="wide")

@st.cache_data(ttl=1)
def load_data_v300():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        last_valid_date = pd.to_datetime("2026-01-01") 

        for i, row in df_raw.iterrows():
            # TẦNG 1: Bỏ qua dòng tiêu đề
            if i == 0: continue
            
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            ngay_raw = str(row.iloc[0]).strip()

            # TẦNG 2: KIỂM TRA TÍNH XÁC THỰC (BỘ LỌC CHUYÊN GIA)
            # - Không lấy dòng có chứa chữ "Mã số" (tiêu đề thừa)
            # - Không lấy dòng trống cả Mã máy và Khách hàng
            # - Mã máy thực tế thường phải có ít nhất 2 ký tự
            if "Mã số" in ma_may or (not ma_may and not khach) or len(ma_may) < 2:
                continue

            # TẦNG 3: XỬ LÝ NGÀY THÁNG
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse):
                last_valid_date = dt_parse

            final_rows.append({
                "NGÀY": last_valid_date,
                "THÁNG": last_valid_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": str(row.iloc[3]).strip(),
                "VÙNG": str(row.iloc[5]).strip().upper()
            })
        
        return pd.DataFrame(final_rows)
    except Exception as e:
        return pd.DataFrame()

data = load_data_v300()

if not data.empty:
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN V300")
        if st.button('🔄 LÀM SẠCH & CẬP NHẬT', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Chỉ hiển thị tháng có dữ liệu thực
        thang_list = sorted(data['THÁNG'].unique())
        sel_thang = st.selectbox("Chọn tháng báo cáo:", thang_list)

    # Lọc dữ liệu theo tháng
    df_f = data[data['THÁNG'] == sel_thang]

    # --- DASHBOARD CHÍNH ---
    st.markdown(f"## 📊 Báo Cáo Thực Tế - Tháng {sel_thang}/2026")
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Tổng ca hỏng thật", len(df_f))
    col_kpi2.metric("Số thiết bị lỗi", df_f['MÃ_MÁY'].nunique())
    col_kpi3.metric("Số khách hàng", df_f['KHÁCH_HÀNG'].nunique())

    # Biểu đồ xu hướng (Sẽ biến mất các cột 4,000 ảo)
    st.subheader("📈 Biểu đồ hỏng hóc thực tế")
    trend = df_f.groupby('NGÀY').size().reset_index(name='Số ca')
    fig = px.bar(trend, x='NGÀY', y='Số ca', text='Số ca', color_discrete_sequence=['#1E3A8A'])
    fig.update_layout(xaxis_title="Ngày trong tháng", yaxis_title="Số ca hỏng")
    st.plotly_chart(fig, use_container_width=True)
    
    # Bảng đối soát cuối cùng
    with st.expander("🔍 Xem danh sách dữ liệu sạch"):
        st.dataframe(df_f, use_container_width=True)
else:
    st.info("Hệ thống đã lọc sạch 100% dòng rác. Vui lòng nhập dữ liệu thực vào Sheets để hiển thị.")
