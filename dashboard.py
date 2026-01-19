import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN CHUẨN (HÌNH 2)
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi 2026", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    div[data-testid="stMetric"] {
        background-color: white; border-radius: 10px; padding: 15px;
        border-left: 5px solid #1E3A8A; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v220():
    try:
        # Thêm timestamp để ép Google Sheets làm mới dữ liệu
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        # BIẾN GHI NHỚ NGÀY (Quan trọng nhất)
        last_date_obj = None
        
        for i, row in df_raw.iterrows():
            # Bỏ qua dòng tiêu đề
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_str = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- BƯỚC 1: CHỈ LẤY DÒNG CÓ MÃ MÁY (LOẠI BỎ 1,669 CA ẢO) ---
            if not ma_may or ma_may.lower() in ["nan", ""]:
                continue 

            # --- BƯỚC 2: THUẬT TOÁN LAST KNOWN DATE ---
            # Nếu ô ngày có dữ liệu, cập nhật ngày mới
            if ngay_str != "":
                temp_date = pd.to_datetime(ngay_str, dayfirst=True, errors='coerce')
                if pd.notnull(temp_date):
                    last_date_obj = temp_date
            
            # Nếu ô ngày trống, dùng lại ngày đã lưu trước đó. 
            # Nếu chưa có ngày nào (dòng đầu trống), mặc định 01/01/2026
            current_date = last_date_obj if last_date_obj else pd.to_datetime("2026-01-01")

            # Phân loại vùng miền
            v_final = "KHÁC"
            if "BẮC" in vung_raw: v_final = "MIỀN BẮC"
            elif "TRUNG" in vung_raw: v_final = "MIỀN TRUNG"
            elif "NAM" in vung_raw: v_final = "MIỀN NAM"

            final_rows.append({
                "NGÀY": current_date.strftime('%d/%m/%Y'),
                "DATE_KEY": current_date,
                "THÁNG": current_date.month,
                "NĂM": current_date.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk,
                "VÙNG": v_final
            })

        return pd.DataFrame(final_rows)
    except Exception as e:
        st.error(f"Lỗi nạp liệu: {e}")
        return None

data = load_data_v220()

if data is not None and not data.empty:
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN")
        if st.button('🔄 LÀM MỚI DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Lọc theo Năm 2026
        df_2026 = data[data['NĂM'] == 2026]
        
        list_thang = ["Tất cả năm 2026"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Chọn kỳ báo cáo", list_thang)

    # Thực hiện lọc Tháng
    if sel_m == "Tất cả năm 2026":
        df_filtered = df_2026
    else:
        m_num = int(sel_m.replace("Tháng ", ""))
        df_filtered = df_2026[df_2026['THÁNG'] == m_num]

    # --- HIỂN THỊ KPI (THEO HÌNH SẾP GỬI) ---
    st.title(f"📊 {sel_m}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
    c2.metric("Số thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    
    re_counts = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn (>1)", len(re_counts[re_counts > 1]))
    c4.metric("Khách hàng báo lỗi", df_filtered['KHÁCH_HÀNG'].nunique())

    # --- BIỂU ĐỒ ---
    tab1, tab2 = st.tabs(["📉 XU HƯỚNG & VÙNG MIỀN", "🔍 DANH SÁCH CHI TIẾT"])
    
    with tab1:
        col_l, col_r = st.columns([1.6, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi theo ngày")
            trend = df_filtered.groupby('DATE_KEY').size().reset_index(name='Số ca')
            fig_line = px.line(trend.sort_values('DATE_KEY'), x='DATE_KEY', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#1E3A8A', marker=dict(size=8))
            st.plotly_chart(fig_line, use_container_width=True)
                        
        with col_r:
            st.subheader("📍 Tỷ lệ Vùng Miền")
            fig_pie = px.pie(df_filtered, names='VÙNG', hole=0.6, 
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#EF4444', 'KHÁC':'#CBD5E1'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with tab2:
        st.write("Dữ liệu đã xử lý ngày tiếp diễn:")
        st.dataframe(df_filtered[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
else:
    st.warning("Đang đợi dữ liệu từ Google Sheets hoặc không có ca hỏng nào trong năm 2026.")
