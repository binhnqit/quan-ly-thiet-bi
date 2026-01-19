import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH HỆ THỐNG PRO V110 ---
st.set_page_config(page_title="Phân Tích Lỗi Thiết Bị - V1100", layout="wide")

@st.cache_data(ttl=1)
def load_data_v1100_final():
    try:
        # Giữ nguyên kết nối trơn tru với Google Sheets
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_records = []
        current_date = None

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua header
            
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            ten_kh = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- 1. XỬ LÝ NGÀY THÁNG (LOGIC MỚI) ---
            # Chỉ cập nhật ngày khi thấy ô Ngày có giá trị hợp lệ
            parsed_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                current_date = parsed_date

            # --- 2. CHỐT CHẶN BỨC PHÁ (QUAN TRỌNG NHẤT) ---
            # Nếu KHÔNG CÓ mã máy HOẶC mã máy là tiêu đề rác -> BỎ QUA NGAY
            if not ma_may or "Mã số" in ma_may or "Mã máy" in ma_may or len(ma_may) < 2:
                continue
            
            # --- 3. CHỈ LƯU KHI CÓ ĐỦ NGÀY VÀ MÃ MÁY ---
            if current_date:
                valid_records.append({
                    "NGÀY_DT": current_date,
                    "NĂM": current_date.year,
                    "THÁNG": current_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": ten_kh if ten_kh else "N/A",
                    "LINH_KIỆN": linh_kien if linh_kien else "Chưa ghi nhận",
                    "VÙNG": "MIỀN BẮC" if "BẮC" in vung_raw else ("MIỀN TRUNG" if "TRUNG" in vung_raw else "MIỀN NAM")
                })
        
        return pd.DataFrame(valid_records)
    except:
        return pd.DataFrame()

# --- KHỞI CHẠY ---
df = load_data_v1100_final()

if not df.empty:
    with st.sidebar:
        st.markdown("### ⚙️ QUẢN TRỊ DỮ LIỆU")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU THỰC', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    # --- HIỂN THỊ KPI CHUẨN ---
    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Tổng ca hỏng THỰC", len(df_final))
    with c2: st.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    with c3: 
        st.metric("Hỏng tái diễn", re_fail)
        if re_fail > 0: st.error("⚠️ Cảnh báo Re-fail")
    with c4: st.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG & VÙNG MIỀN", "🚩 QUẢN TRỊ RỦI RO", "🔍 TRUY XUẤT", "📁 DỮ LIỆU SẠCH"])

    with t1:
        col_l, col_r = st.columns([1.6, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi theo thời gian")
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)
            

        with col_r:
            st.subheader("📍 Tỷ lệ theo Vùng")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                             color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("🔧 Phân tích linh kiện")
        lk = df_final['LINH_KIỆN'].value_counts().reset_index().head(10)
        fig_bar = px.bar(lk, x='count', y='LINH_KIỆN', orientation='h', text='count')
        fig_bar.update_traces(marker_color='#1E3A8A')
        st.plotly_chart(fig_bar, use_container_width=True)
        

    with t2:
        st.subheader("🚩 Thiết bị hỏng lặp lại")
        st.dataframe(dup[dup > 1], use_container_width=True)

    with t3:
        q = st.text_input("Tìm Mã máy hoặc Khách hàng:")
        if q:
            st.dataframe(df[df['MÃ_MÁY'].str.contains(q, case=False) | df['KHÁCH_HÀNG'].str.contains(q, case=False)], use_container_width=True)

    with t4:
        st.subheader("📁 Đối soát dữ liệu (Dòng thực tế)")
        st.dataframe(df_final, use_container_width=True)

else:
    st.info("Hệ thống đã dọn sạch 100% dòng rác. Đang chờ sếp nhập dữ liệu thực tế vào Sheets.")
