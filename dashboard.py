import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Báo Cáo Chuẩn 2026", layout="wide")

@st.cache_data(ttl=1)
def load_data_v260():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        last_date = pd.to_datetime("2026-01-01") 
        
        for i, row in df_raw.iterrows():
            # Bỏ qua tiêu đề
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung = str(row.iloc[5]).strip().upper()

            # --- BỘ LỌC TỐI THƯỢNG (FIX CON SỐ 4,000) ---
            # Chỉ lấy dòng nếu sếp đã nhập ít nhất là Mã máy HOẶC Khách hàng
            if len(ma_may) < 2 and len(khach) < 2:
                continue 

            # Logic ngày tiếp diễn
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse):
                last_date = dt_parse

            final_rows.append({
                "NGÀY_DT": last_date,
                "NGÀY_HIỂN_THỊ": last_date.strftime('%d/%m/%Y'),
                "THÁNG": last_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung else ("MIỀN TRUNG" if "TRUNG" in vung else "MIỀN NAM")
            })
        return pd.DataFrame(final_rows)
    except:
        return pd.DataFrame()

data = load_data_v260()

if not data.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V260")
        if st.button('🔄 ĐỒNG BỘ LẠI SHEET', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Sếp chọn "Tất cả" hoặc từng tháng
        list_thang = ["Tất cả"] + sorted([str(m) for m in data['THÁNG'].unique()])
        sel_m = st.selectbox("Chọn Tháng:", list_thang)

    # Lọc dữ liệu
    df_f = data.copy()
    if sel_m != "Tất cả":
        df_f = df_f[df_f['THÁNG'] == int(sel_m)]

    # --- KPI CHUẨN ---
    st.markdown(f"## 📊 Kết quả thực tế: {sel_m if sel_m == 'Tất cả' else 'Tháng ' + sel_m}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng thực", f"{len(df_f)}")
    c2.metric("Số máy lỗi", df_f['MÃ_MÁY'].nunique())
    
    dup = df_f['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn", len(dup[dup > 1]))
    c4.metric("Linh kiện lỗi nhất", df_f['LINH_KIỆN'].mode()[0] if not df_f.empty else "N/A")

    # --- BIỂU ĐỒ ---
    col1, col2 = st.columns([1.6, 1])
    with col1:
        st.subheader("📈 Biểu đồ hỏng hóc (Theo ngày)")
        trend = df_f.groupby('NGÀY_DT').size().reset_index(name='Số ca')
        # Dùng Bar chart để sếp thấy rõ từng ngày lẻ
        fig = px.bar(trend, x='NGÀY_DT', y='Số ca', text='Số ca')
        fig.update_traces(marker_color='#1E3A8A', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
                
    with col2:
        st.subheader("📍 Phân bổ Vùng Miền")
        fig_pie = px.pie(df_f, names='VÙNG', hole=0.6, 
                         color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#EF4444'})
        st.plotly_chart(fig_pie, use_container_width=True)

    # Bảng kiểm tra - Sếp sẽ thấy ở đây không còn dòng trống nào
    with st.expander("🔍 Danh sách đã làm sạch (Đối soát tại đây)"):
        st.dataframe(df_f[['NGÀY_HIỂN_THỊ', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
else:
    st.info("Sếp ơi, hãy nhấn 'Đồng bộ lại Sheet' để tôi quét lại dữ liệu nhé!")
