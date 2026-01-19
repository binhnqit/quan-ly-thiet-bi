import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Phần Mềm Quản Lý Lỗi - PRO V800", layout="wide")

@st.cache_data(ttl=0)
def load_data_v800_final():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_records = []
        # Ngày neo (anchor date) - chỉ dùng để kế thừa khi có dữ liệu thực
        anchor_date = None 

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua header
            
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            ten_kh = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- BƯỚC 1: XÁC ĐỊNH NGÀY NEO ---
            # Nếu ô ngày có dữ liệu, cập nhật ngày neo mới
            parsed_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                anchor_date = parsed_date

            # --- BƯỚC 2: BỘ LỌC BỨC PHÁ (CHỐT CHẶN SAI SỐ) ---
            # Chỉ xử lý dòng nếu có Mã máy thực sự (loại bỏ dòng rác, dòng tiêu đề, dòng trống)
            if not ma_may or "Mã số" in ma_may or len(ma_may) < 2:
                continue
            
            # --- BƯỚC 3: GÁN DỮ LIỆU ---
            # Nếu dòng có mã máy nhưng anchor_date vẫn trống (dòng đầu tiên lỗi), lấy 01/01/2026
            final_date = anchor_date if anchor_date else pd.to_datetime("2026-01-01")

            valid_records.append({
                "NGÀY_DT": final_date,
                "NĂM": final_date.year,
                "THÁNG": final_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": ten_kh if ten_kh else "N/A",
                "LINH_KIỆN": linh_kien if linh_kien else "Chưa ghi nhận",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung_raw else ("MIỀN TRUNG" if "TRUNG" in vung_raw else "MIỀN NAM")
            })
        
        return pd.DataFrame(valid_records)
    except:
        return pd.DataFrame()

df = load_data_v800_final()

# --- GIAO DIỆN CHỨC NĂNG (ĐÚNG NHƯ HÌNH ĐÍNH KÈM) ---
if not df.empty:
    with st.sidebar:
        st.markdown("### ⚙️ QUẢN TRỊ HỆ THỐNG")
        if st.button('🔄 LÀM SẠCH & ĐỒNG BỘ', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("📅 Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Chọn Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    st.title("📊 Hệ Thống Phân Tích Lỗi Thiết Bị")

    # KPI CHUẨN (Hàng ngang)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    c3.metric("Hỏng tái diễn (>1)", re_fail)
    c4.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

    # TABS (Như hình V110)
    t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG & VÙNG MIỀN", "🚩 RE-FAIL", "🔍 TRUY XUẤT", "📁 DỮ LIỆU SẠCH"])

    with t1:
        col_l, col_r = st.columns([1.6, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi hằng ngày")
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)
            

        with col_r:
            st.subheader("📍 Tỷ lệ theo Vùng")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                             color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("🔧 Phân tích linh kiện")
        lk = df_final['LINH_KIỆN'].value_counts().reset_index()
        fig_bar = px.bar(lk, x='count', y='LINH_KIỆN', orientation='h', text='count')
        fig_bar.update_traces(marker_color='#1E3A8A')
        st.plotly_chart(fig_bar, use_container_width=True)
        

    with t2:
        st.subheader("🚩 Danh sách thiết bị báo động Re-fail")
        st.dataframe(dup[dup > 1], use_container_width=True)

    with t3:
        search = st.text_input("🔍 Nhập Mã máy hoặc Tên KH để tra cứu:")
        if search:
            res = df[df['MÃ_MÁY'].str.contains(search, case=False) | df['KHÁCH_HÀNG'].str.contains(search, case=False)]
            st.dataframe(res, use_container_width=True)

    with t4:
        st.subheader("📁 Đối soát dữ liệu thực thực tế")
        st.dataframe(df_final, use_container_width=True)

else:
    st.info("Hệ thống đã loại bỏ 100% dòng trống. Vui lòng kiểm tra dữ liệu thực trong Sheets.")
