import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH GIAO DIỆN CHUẨN ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=1)
def load_data_v600_ultimate():
    try:
        # Giữ nguyên phần kết nối đã chạy tốt
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_records = []
        current_date = pd.to_datetime("2026-01-01") # Mặc định khởi tạo

        for i, row in df_raw.iterrows():
            # 1. TRUY XUẤT GIÁ TRỊ CÁC CỘT
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            ten_kh = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # 2. CẬP NHẬT NGÀY THÁNG (Chỉ cập nhật khi dòng đó thực sự có ghi ngày mới)
            temp_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            if pd.notnull(temp_date):
                current_date = temp_date

            # 3. CHỐT CHẶN "BỨC PHÁ": KIỂM TRA MÃ MÁY THỰC
            # Loại bỏ: Dòng trống, Dòng tiêu đề, Dòng chứa chữ "Mã số"
            if not ma_may or "Mã số" in ma_may or "Mã máy" in ma_may or len(ma_may) < 2:
                continue
            
            # 4. GHI NHẬN DỮ LIỆU SẠCH
            valid_records.append({
                "NGÀY_DT": current_date,
                "NĂM": current_date.year,
                "THÁNG": current_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": ten_kh if ten_kh else "Khách vãng lai",
                "LINH_KIỆN": linh_kien if linh_kien else "Chưa xác định",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung_mien else ("MIỀN TRUNG" if "TRUNG" in vung_mien else "MIỀN NAM")
            })
        
        return pd.DataFrame(valid_records)
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

# --- KHỞI CHẠY HỆ THỐNG ---
df = load_data_v600_ultimate()

if not df.empty:
    with st.sidebar:
        st.markdown("### ⚙️ HỆ QUẢN TRỊ V600")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU THỰC', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        list_year = sorted(df['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", list_year)
        
        df_year = df[df['NĂM'] == sel_year]
        list_month = ["Tất cả"] + sorted(df_year['THÁNG'].unique().tolist())
        sel_month = st.selectbox("🗓️ Chọn Tháng", list_month)
        
        df_final = df_year if sel_month == "Tất cả" else df_year[df_year['THÁNG'] == sel_month]

    # --- HIỂN THỊ KPI (THEO ĐÚNG HÌNH SẾP DUYỆT) ---
    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Tổng ca hỏng thực", len(df_final))
    with c2: st.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup_counts = df_final['MÃ_MÁY'].value_counts()
    refail = len(dup_counts[dup_counts > 1])
    with c3: 
        st.metric("Hỏng tái diễn (>1)", refail)
        if refail > 0: st.warning("⚠️ Cần kiểm tra kỹ")
    with c4: st.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

    # --- TABS CHỨC NĂNG ---
    t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG & VÙNG MIỀN", "🚩 RỦI RO (RE-FAIL)", "🔍 TRUY XUẤT", "📁 DỮ LIỆU SẠCH"])

    with t1:
        col_l, col_r = st.columns([1.6, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi thực tế")
            # Group theo ngày để vẽ biểu đồ đường trơn tru
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#0047AB', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)
            
        with col_r:
            st.subheader("📍 Tỷ lệ Vùng Miền")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                             color_discrete_map={'MIỀN BẮC':'#1F77B4', 'MIỀN NAM':'#FF7F0E', 'MIỀN TRUNG':'#D62728'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("🔧 Linh kiện hay hỏng nhất")
        lk_data = df_final['LINH_KIỆN'].value_counts().reset_index().head(10)
        fig_bar = px.bar(lk_data, x='count', y='LINH_KIỆN', orientation='h', text='count')
        fig_bar.update_traces(marker_color='#0047AB')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with t2:
        st.subheader("🚩 Danh sách thiết bị hỏng lặp lại")
        if refail > 0:
            re_df = dup_counts[dup_counts > 1].reset_index()
            re_df.columns = ['Mã Máy', 'Số lần hỏng']
            st.table(re_df)
        else:
            st.success("Tuyệt vời! Không có thiết bị nào hỏng tái diễn.")

    with t3:
        st.subheader("🔍 Tìm kiếm lịch sử máy")
        query = st.text_input("Nhập Mã máy hoặc Tên KH:")
        if query:
            search_df = df[df['MÃ_MÁY'].str.contains(query, case=False) | df['KHÁCH_HÀNG'].str.contains(query, case=False)]
            st.dataframe(search_df, use_container_width=True)

    with t4:
        st.subheader("📁 Đối soát dữ liệu đã làm sạch")
        st.dataframe(df_final, use_container_width=True)

else:
    st.info("Hệ thống đã loại bỏ rác thành công. Đang chờ dữ liệu thực tế từ Google Sheets của sếp.")
