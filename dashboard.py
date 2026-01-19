import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. GIAO DIỆN CHUẨN EXECUTIVE (HÌNH 2)
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi 2026", layout="wide")

@st.cache_data(ttl=1)
def load_data_v180():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        last_valid_date = pd.to_datetime("01/01/2026", dayfirst=True) # Mặc định đầu năm
        
        for i, row in df_raw.iterrows():
            # Bỏ qua tiêu đề
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            # ĐỌC DỮ LIỆU GỐC
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_f = str(row.iloc[5]).strip().upper()

            # --- CẢI TIẾN QUAN TRỌNG: CHỈ LẤY DÒNG CÓ MÃ MÁY ---
            if not ma_may or ma_may.lower() == "nan" or len(ma_may) < 2:
                continue # Bỏ qua dòng trống hoàn toàn để tránh tăng số ảo

            # Xử lý điền ngày thông minh
            dt_obj = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_obj):
                last_valid_date = dt_obj
            else:
                dt_obj = last_valid_date 

            final_rows.append({
                "NGÀY": dt_obj.strftime('%d/%m/%Y'),
                "DATE_KEY": dt_obj,
                "THÁNG": dt_obj.month,
                "NĂM": dt_obj.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": vung_f if vung_f else "KHÁC"
            })

        df = pd.DataFrame(final_rows)
        # Chuẩn hóa vùng miền theo Cột F (Giống hình sếp gửi)
        df['VÙNG_CHỈNH'] = df['VÙNG'].apply(lambda x: "MIỀN BẮC" if "BẮC" in x else ("MIỀN TRUNG" if "TRUNG" in x else ("MIỀN NAM" if "NAM" in x else "KHÁC")))
        return df
    except Exception as e:
        return None

data = load_data_v180()

if data is not None:
    # Sidebar
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_m = st.selectbox("Chọn tháng", ["Tất cả/2026"] + [f"Tháng {i}" for i in range(1, 13)])

    # Lọc chuẩn theo Năm 2026 và Tháng đã chọn
    df_2026 = data[data['NĂM'] == 2026]
    if sel_m == "Tất cả/2026":
        df_filtered = df_2026
    else:
        m_num = int(sel_m.replace("Tháng ", ""))
        df_filtered = df_2026[df_2026['THÁNG'] == m_num]

    # --- HIỂN THỊ KPI (THEO GIAO DIỆN HÌNH 2) ---
    st.markdown(f"## 📊 Báo Cáo Tài Sản: {sel_m}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
    c2.metric("Thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    
    re_counts = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn (>1)", len(re_counts[re_counts > 1]))
    c4.metric("Khách hàng báo lỗi", df_filtered['KHÁCH_HÀNG'].nunique())

    # --- BIỂU ĐỒ ---
    tab1, tab2 = st.tabs(["📉 XU HƯỚNG & VÙNG MIỀN", "📋 CHI TIẾT DỮ LIỆU"])
    
    with tab1:
        col_l, col_r = st.columns([1.5, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi thực tế")
            trend = df_filtered.groupby('DATE_KEY').size().reset_index(name='Số ca')
            fig_line = px.line(trend.sort_values('DATE_KEY'), x='DATE_KEY', y='Số ca', markers=True, color_discrete_sequence=['#1E3A8A'])
            st.plotly_chart(fig_line, use_container_width=True)
                        
        with col_r:
            st.subheader("📍 Tỷ lệ Vùng Miền (Cột F)")
            fig_pie = px.pie(df_filtered, names='VÙNG_CHỈNH', hole=0.6, 
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#EF4444'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with tab2:
        st.dataframe(df_filtered[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG_CHỈNH']], use_container_width=True)
