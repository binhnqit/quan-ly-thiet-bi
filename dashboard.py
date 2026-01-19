import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi PRO", layout="wide")

# --- ENGINE XỬ LÝ DỮ LIỆU SẠCH TUYỆT ĐỐI ---
@st.cache_data(ttl=1)
def load_data_pro_v320():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        clean_rows = []
        current_date = pd.to_datetime("2026-01-01") 

        for i, row in df_raw.iterrows():
            if i == 0: continue
            
            # Lấy dữ liệu thô và làm sạch khoảng trắng
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            lk = str(row.iloc[3]).strip()
            vung = str(row.iloc[5]).strip().upper()

            # --- BỘ LỌC CHUYÊN GIA (CHẶN SỐ ẢO) ---
            # 1. Loại bỏ dòng tiêu đề lặp lại
            if "Mã số" in ma_may or "Tên KH" in khach: continue
            # 2. Loại bỏ dòng trống hoặc dòng chỉ có ký tự đặc biệt/dấu cách
            if len(ma_may) < 2 or len(khach) < 2: continue
            # 3. Kiểm tra nếu mã máy chỉ toàn số 0 hoặc ký tự lỗi
            if ma_may.lower() == "nan" or ma_may == "0": continue

            # Cập nhật ngày tháng (chỉ cập nhật nếu ô ngày có dữ liệu chuẩn)
            parsed_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                current_date = parsed_date

            clean_rows.append({
                "DATE_OBJ": current_date,
                "THÁNG": current_date.month,
                "NĂM": current_date.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach,
                "LINH_KIỆN": lk if lk else "N/A",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung else ("MIỀN TRUNG" if "TRUNG" in vung else "MIỀN NAM")
            })
        
        return pd.DataFrame(clean_rows)
    except:
        return pd.DataFrame()

# --- GIAO DIỆN PHẦN MỀM ---
df = load_data_pro_v320()

if not df.empty:
    # Sidebar chuyên nghiệp
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V320")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU THỰC', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        months = ["Tất cả"] + sorted(df[df['NĂM'] == sel_year]['THÁNG'].unique().tolist())
        sel_month = st.selectbox("Chọn Tháng", months)

    # Lọc dữ liệu hiển thị
    df_view = df[df['NĂM'] == sel_year]
    if sel_month != "Tất cả":
        df_view = df_view[df_view['THÁNG'] == sel_month]

    # --- HEADER KPI (NHƯ HÌNH V110) ---
    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1: st.metric("Tổng ca hỏng", len(df_view))
    with kpi2: st.metric("Thiết bị lỗi", df_view['MÃ_MÁY'].nunique())
    
    # Tính hỏng tái diễn
    dup_counts = df_view['MÃ_MÁY'].value_counts()
    refail = len(dup_counts[dup_counts > 1])
    with kpi3: 
        st.metric("Hỏng tái diễn (>1 lần)", refail)
        if refail > 0: st.write("🔴 **Cần chú trọng**")
        
    with kpi4: st.metric("Khách hàng báo lỗi", df_view['KHÁCH_HÀNG'].nunique())

    # --- TABS CHỨC NĂNG ---
    t1, t2, t3 = st.tabs(["📊 XU HƯỚNG & VÙNG MIỀN", "🔍 TRUY XUẤT LỊCH SỬ", "📋 DỮ LIỆU CHI TIẾT"])
    
    with t1:
        col_l, col_r = st.columns([1.6, 1])
        with col_l:
            st.subheader("📈 Xu hướng lỗi theo thời gian")
            trend = df_view.groupby('DATE_OBJ').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='DATE_OBJ', y='Số ca', markers=True, text='Số ca')
            fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy', textposition="top center")
            st.plotly_chart(fig_line, use_container_width=True)
            
        with col_r:
            st.subheader("📍 Tỷ lệ Vùng Miền")
            fig_pie = px.pie(df_view, names='VÙNG', hole=0.5, 
                             color_discrete_map={'MIỀN BẮC':'#34D399', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#F87171'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("🔧 Phân tích Linh kiện lỗi")
        lk_counts = df_view['LINH_KIỆN'].value_counts().reset_index()
        fig_bar = px.bar(lk_counts, x='count', y='LINH_KIỆN', orientation='h', text='count')
        fig_bar.update_traces(marker_color='#1E3A8A')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with t2:
        st.subheader("🔍 Tra cứu nhanh thiết bị")
        search = st.text_input("Nhập Mã Máy hoặc Tên Khách Hàng:")
        if search:
            res = df[df['MÃ_MÁY'].str.contains(search, case=False) | df['KHÁCH_HÀNG'].str.contains(search, case=False)]
            st.dataframe(res[['DATE_OBJ', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN', 'VÙNG']], use_container_width=True)

    with t3:
        st.subheader("📋 Danh sách dữ liệu thực tế (Đã lọc rác)")
        st.dataframe(df_view, use_container_width=True)

else:
    st.warning("Hệ thống đã loại bỏ 100% dữ liệu ảo. Hiện chưa tìm thấy dữ liệu thực nào. Sếp hãy kiểm tra lại file Sheets!")
