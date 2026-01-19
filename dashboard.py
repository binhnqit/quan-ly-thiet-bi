import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH HỆ THỐNG PRO V110 ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=1)
def load_data_radical_change():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        # Đọc dữ liệu và ép kiểu string để tránh lỗi định dạng
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_data = []
        last_valid_date = None

        for i, row in df_raw.iterrows():
            # 1. LOẠI BỎ DÒNG TIÊU ĐỀ VÀ DÒNG TRỐNG (THAY ĐỔI LỚN Ở ĐÂY)
            ma_may = str(row.iloc[1]).strip()
            # Nếu không có Mã máy, hoặc là chữ "Mã số máy", hoặc độ dài quá ngắn -> BỎ QUA LUÔN
            if not ma_may or "Mã" in ma_may or len(ma_may) < 2:
                continue
            
            # 2. XỬ LÝ NGÀY THÁNG CHỈ CHO DÒNG CÓ DỮ LIỆU THỰC
            raw_date = str(row.iloc[0]).strip()
            parsed_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            
            if pd.notnull(parsed_date):
                last_valid_date = parsed_date
            
            # Nếu dòng có mã máy mà không có ngày, lấy ngày valid gần nhất
            final_date = last_valid_date if last_valid_date else pd.to_datetime("2026-01-01")

            valid_data.append({
                "NGÀY_DT": final_date,
                "NĂM": final_date.year,
                "THÁNG": final_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": str(row.iloc[2]).strip(),
                "LINH_KIỆN": str(row.iloc[3]).strip(),
                "VÙNG": str(row.iloc[5]).strip().upper()
            })
        
        return pd.DataFrame(valid_data)
    except:
        return pd.DataFrame()

# --- GIAO DIỆN ĐIỀU KHIỂN ---
df = load_ радика_change()

# Chuẩn hóa vùng miền để vẽ biểu đồ
if not df.empty:
    df['VÙNG_FIX'] = df['VÙNG'].apply(lambda x: "MIỀN BẮC" if "BẮC" in x else ("MIỀN TRUNG" if "TRUNG" in x else "MIỀN NAM"))

with st.sidebar:
    st.markdown("### ⚙️ QUẢN TRỊ V110")
    if st.button('🔄 ĐỒNG BỘ DỮ LIỆU MỚI', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if not df.empty:
        st.divider()
        sel_year = st.selectbox("📅 Năm báo cáo", sorted(df['NĂM'].unique(), reverse=True))
        df_year = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Tháng báo cáo", ["Tất cả"] + sorted(df_year['THÁNG'].unique().tolist()))
        
        df_final = df_year if sel_month == "Tất cả" else df_year[df_year['THÁNG'] == sel_month]
    else:
        st.error("Không tìm thấy dữ liệu thực tế!")
        st.stop()

# --- HIỂN THỊ CHỨC NĂNG (THEO HÌNH image_f7d89c) ---
st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")

# Hàng KPI
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Tổng ca hỏng", len(df_final))
with c2: st.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
dup_counts = df_final['MÃ_MÁY'].value_counts()
refail = len(dup_counts[dup_counts > 1])
with c3: 
    st.metric("Hỏng tái diễn (>1)", refail)
    if refail > 0: st.markdown("🔴 **Cần chú trọng**")
with c4: st.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

# Hệ thống Tabs chuẩn PRO
t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG & PHÂN BỐ", "🚩 QUẢN TRỊ RỦI RO", "🔍 TRUY XUẤT", "📁 DỮ LIỆU SẠCH"])

with t1:
    col_l, col_r = st.columns([1.6, 1])
    with col_l:
        st.subheader("📈 Diễn biến hỏng hóc thực tế")
        trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
        fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
        fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy')
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col_r:
        st.subheader("📍 Tỷ lệ Vùng Miền")
        fig_pie = px.pie(df_final, names='VÙNG_FIX', hole=0.5, 
                         color_discrete_map={'MIỀN BẮC':'#34D399', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#F87171'})
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    st.subheader("🔧 Phân tích Linh kiện lỗi")
    lk_data = df_final['LINH_KIỆN'].value_counts().reset_index()
    fig_bar = px.bar(lk_data, x='count', y='LINH_KIỆN', orientation='h', text='count')
    fig_bar.update_traces(marker_color='#1E3A8A')
    st.plotly_chart(fig_bar, use_container_width=True)

with t2:
    st.subheader("🚩 Danh sách thiết bị báo động (Re-fail)")
    st.dataframe(dup_counts[dup_counts > 1], use_container_width=True)

with t3:
    st.subheader("🔍 Truy xuất nhanh")
    search = st.text_input("Nhập Mã máy/Khách hàng:")
    if search:
        st.dataframe(df[df['MÃ_MÁY'].str.contains(search, case=False) | df['KHÁCH_HÀNG'].str.contains(search, case=False)], use_container_width=True)

with t4:
    st.subheader("📁 Đối soát dữ liệu chi tiết")
    st.dataframe(df_final, use_container_width=True)
