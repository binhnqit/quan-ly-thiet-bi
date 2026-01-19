import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=0) # Ép bộ nhớ đệm về 0 để làm mới hoàn toàn
def load_data_v700_final():
    try:
        # Giữ nguyên kết nối Sheets trơn tru
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_records = []
        temp_date = None

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ header
            
            # Đọc dữ liệu thô
            raw_ngay = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach_hang = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # --- GIẢI PHÁP BỨC PHÁ: CHỈ LẤY DÒNG CÓ MÃ MÁY VÀ KHÁCH HÀNG ---
            # Nếu dòng này trống cả mã máy và khách hàng -> Dòng rác, dừng đọc tại đây hoặc bỏ qua
            if not ma_may and not khach_hang:
                continue
            
            # Cập nhật ngày tháng nếu có ngày mới
            current_date_parsed = pd.to_datetime(raw_ngay, dayfirst=True, errors='coerce')
            if pd.notnull(current_date_parsed):
                temp_date = current_date_parsed
            
            # Nếu đã có ngày (từ dòng này hoặc dòng trên kéo xuống) và có mã máy
            if temp_date and ma_may and ma_may.lower() != "mã số máy":
                valid_records.append({
                    "NGÀY_DT": temp_date,
                    "NĂM": temp_date.year,
                    "THÁNG": temp_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": khach_hang if khach_hang else "N/A",
                    "LINH_KIỆN": linh_kien if linh_kien else "Chưa ghi nhận",
                    "VÙNG": "MIỀN BẮC" if "BẮC" in vung_mien else ("MIỀN TRUNG" if "TRUNG" in vung_mien else "MIỀN NAM")
                })
        
        return pd.DataFrame(valid_records)
    except Exception as e:
        return pd.DataFrame()

# --- XỬ LÝ DỮ LIỆU ---
df = load_data_v700_final()

if not df.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V700")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU THẬT', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("Chọn Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    # --- KPI CHUẨN ---
    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Tổng ca hỏng THỰC", len(df_final))
    with c2: st.metric("Số máy lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    with c3: 
        st.metric("Hỏng tái diễn", re_fail)
        if re_fail > 0: st.error("⚠️ Cảnh báo Re-fail")
    with c4: st.metric("Số khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["📊 BIỂU ĐỒ THỰC", "🚩 RỦI RO", "🔍 TRUY XUẤT", "📁 DỮ LIỆU SẠCH"])

    with t1:
        col1, col2 = st.columns([1.6, 1])
        with col1:
            st.subheader("📈 Xu hướng lỗi (Đã lọc rác)")
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#0047AB', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)

        with col2:
            st.subheader("📍 Phân bổ Vùng Miền")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                             color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        st.subheader("🚩 Danh sách Re-fail")
        st.write(dup[dup > 1])

    with t3:
        search = st.text_input("Tìm kiếm Mã máy/Khách hàng:")
        if search:
            st.dataframe(df[df['MÃ_MÁY'].str.contains(search, case=False) | df['KHÁCH_HÀNG'].str.contains(search, case=False)])

    with t4:
        st.subheader("📁 Đối soát dòng dữ liệu thực tế")
        st.dataframe(df_final, use_container_width=True)
else:
    st.info("Hệ thống đã loại bỏ hoàn toàn dòng ảo. Vui lòng kiểm tra lại dữ liệu nhập trong Sheets.")
