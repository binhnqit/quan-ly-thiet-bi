import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi 2026", layout="wide")

# 1. URL DỮ LIỆU GỐC
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v240():
    try:
        # Ép làm mới bằng timestamp để xóa cache 1,669 ảo
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        # Biến "nhớ" ngày: Nếu dòng trên có ngày, dòng dưới trống thì dùng lại ngày đó
        current_active_date = None 
        
        for i, row in df_raw.iterrows():
            # Bỏ qua tiêu đề
            if i == 0 or "Mã số" in str(row.iloc[1]): continue
            
            ngay_raw = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- ĐIỀU KIỆN 1: CHỈ LẤY DÒNG CÓ MÃ MÁY (Xử lý con số 1,639 ảo) ---
            if not ma_may or ma_may.lower() == "nan": continue

            # --- ĐIỀU KIỆN 2: XỬ LÝ NGÀY THÔNG MINH ---
            if ngay_raw != "":
                # Thử đọc nhiều định dạng ngày khác nhau để không bị kẹt ở 01/01
                new_date = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
                if pd.notnull(new_date):
                    current_active_date = new_date
            
            # Nếu vẫn không có ngày nào (dòng đầu trống), lấy đại diện 01/01/2026
            display_date = current_active_date if current_active_date else pd.to_datetime("2026-01-01")

            # Phân loại vùng
            v_final = "MIỀN BẮC" if "BẮC" in vung_raw else ("MIỀN TRUNG" if "TRUNG" in vung_raw else "MIỀN NAM")

            final_rows.append({
                "DATE_OBJ": display_date,
                "NGÀY": display_date.strftime('%d/%m/%Y'),
                "THÁNG": display_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": str(row.iloc[2]).strip(),
                "LINH_KIỆN": str(row.iloc[3]).strip(),
                "VÙNG": v_final
            })
        
        return pd.DataFrame(final_rows)
    except:
        return pd.DataFrame()

data = load_data_v240()

if not data.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V240")
        if st.button('🔄 LÀM MỚI DỮ LIỆU NGAY', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Bộ lọc tháng
        thang_list = ["Tất cả"] + sorted(data['THÁNG'].unique().tolist())
        sel_thang = st.selectbox("Chọn Tháng báo cáo", thang_list)

    # Lọc dữ liệu
    df_f = data.copy()
    if sel_thang != "Tất cả":
        df_f = df_f[df_f['THÁNG'] == sel_thang]

    # --- HIỂN THỊ KPI ---
    st.title(f"📊 Báo Cáo Tài Sản - Tháng {sel_thang}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_f)}")
    c2.metric("Số thiết bị lỗi", df_f['MÃ_MÁY'].nunique())
    
    # Tính hỏng tái diễn
    dup = df_f['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn (>1)", len(dup[dup > 1]))
    c4.metric("Vùng nhiều lỗi nhất", df_f['VÙNG'].mode()[0] if not df_f.empty else "N/A")

    # --- BIỂU ĐỒ ---
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.subheader("📈 Xu hướng lỗi (Theo từng ngày)")
        # Gom nhóm và đếm theo ngày
        trend = df_f.groupby('DATE_OBJ').size().reset_index(name='Số ca')
        fig = px.line(trend, x='DATE_OBJ', y='Số ca', markers=True, text='Số ca')
        fig.update_traces(line_color='#1E3A8A', textposition="top center")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("📍 Phân bổ Vùng Miền")
        fig_pie = px.pie(df_f, names='VÙNG', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Bảng kiểm tra
    with st.expander("🔍 Xem danh sách đối soát chi tiết"):
        st.dataframe(df_f[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)
else:
    st.error("Không tìm thấy dữ liệu. Sếp hãy kiểm tra lại file Sheets hoặc nhấn 'Làm mới'.")
