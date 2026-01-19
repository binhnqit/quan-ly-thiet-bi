import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Báo Cáo Tài Sản 2026", layout="wide")

# 1. NẠP DỮ LIỆU VỚI CƠ CHẾ LÀM SẠCH SÂU
@st.cache_data(ttl=1)
def load_data_v250():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        last_date = pd.to_datetime("2026-01-01") # Ngày khởi tạo mặc định
        
        for i, row in df_raw.iterrows():
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung = str(row.iloc[5]).strip().upper()

            # --- BỘ LỌC QUAN TRỌNG: Loại bỏ dòng trống sếp không nhập liệu ---
            # Nếu cả 3 cột chính đều trống, ta coi là dòng rác
            if not ma_may and not khach and not lk:
                continue 

            # Cập nhật ngày nếu sếp có nhập ô mới
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse):
                last_date = dt_parse

            final_rows.append({
                "NGÀY": last_date,
                "THÁNG": last_date.month,
                "MÃ_MÁY": ma_may if ma_may else "Chưa ghi mã",
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": "BẮC" if "BẮC" in vung else ("TRUNG" if "TRUNG" in vung else "NAM")
            })
        return pd.DataFrame(final_rows)
    except:
        return pd.DataFrame()

data = load_data_v250()

if not data.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V250")
        if st.button('🔄 ĐỒNG BỘ LẠI SHEET', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Sếp chọn Tháng cụ thể để xem số thực
        list_thang = sorted(data['THÁNG'].unique())
        sel_m = st.selectbox("Xem báo cáo Tháng:", list_thang)

    # Lọc dữ liệu theo tháng chọn
    df_f = data[data['THÁNG'] == sel_m]

    # --- HIỂN THỊ KPI ---
    st.markdown(f"## 📊 Báo Cáo Tài Sản - Tháng {sel_m}/2026")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_f)}")
    c2.metric("Thiết bị lỗi", df_f['MÃ_MÁY'].nunique())
    
    dup = df_f['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn", len(dup[dup > 1]))
    c4.metric("Linh kiện lỗi nhiều nhất", df_f['LINH_KIỆN'].mode()[0] if not df_f.empty else "N/A")

    # --- BIỂU ĐỒ ---
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.subheader("📈 Chi tiết lỗi theo ngày (Tháng " + str(sel_m) + ")")
        trend = df_f.groupby('NGÀY').size().reset_index(name='Số ca')
        fig = px.bar(trend, x='NGÀY', y='Số ca', text='Số ca', color_discrete_sequence=['#1E3A8A'])
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("📍 Phân bổ Vùng Miền")
        fig_pie = px.pie(df_f, names='VÙNG', hole=0.6, 
                         color_discrete_map={'BẮC':'#1E3A8A', 'NAM':'#3B82F6', 'TRUNG':'#EF4444'})
        st.plotly_chart(fig_pie, use_container_width=True)
        
    # Bảng chi tiết để sếp xóa dòng rác nếu cần
    with st.expander("🔍 Kiểm tra danh sách chi tiết"):
        st.dataframe(df_f, use_container_width=True)
else:
    st.warning("Đang kết nối với Google Sheets... Sếp hãy kiểm tra lại quyền chia sẻ file!")
