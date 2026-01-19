import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="AI Quản Trị Tài Sản V63", layout="wide")

# LINK CSV CHUẨN
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v63():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- DÒ CỘT TỰ ĐỘNG ---
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(50)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['3534', '1102', 'MÃ']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA', 'PHÍM']) or df_raw.columns[3]
        c_ng = find_col(['2024', '2025', '2026', '/']) or df_raw.columns[0]
        c_kh = find_col(['QUANG TRUNG', 'SƠN HẢI', 'KHÁCH']) or df_raw.columns[2]
        c_vm = find_col(['MIỀN', 'VÙNG', 'BẮC', 'NAM', 'TRUNG']) or (df_raw.columns[10] if len(df_raw.columns)>10 else None)

        # CHUẨN HÓA DỮ LIỆU
        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw[c_ly].astype(str).str.strip()
        df['NGÀY'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # XỬ LÝ VÙNG MIỀN (Chỉ lấy Bắc, Trung, Nam)
        vm_raw = df_raw[c_vm].astype(str).str.strip() if c_vm else pd.Series([""]*len(df))
        df['VÙNG_MIỀN'] = vm_raw
        
        # --- BỘ LỌC CHUẨN CỦA SẾP ---
        vung_mien_chuan = ['MIỀN BẮC', 'MIỀN TRUNG', 'MIỀN NAM']
        # Chuyển về viết hoa để so khớp chính xác
        df = df[df['VÙNG_MIỀN'].str.upper().isin(vung_mien_chuan)].copy()

        # LÀM SẠCH TIẾP (Mã máy > 2 ký tự, bỏ tên hãng máy)
        df = df[df['MÃ_MÁY'].str.len() >= 3].copy()
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE']
        df = df[~df['LÝ_DO'].str.upper().isin(hang_may)]
        
        df['NĂM'] = df['NGÀY'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY'].dt.month.fillna(1).astype(int)
        df['THÁNG'] = df['THÁNG_NUM'].apply(lambda x: f"Tháng {x}")
        
        return df
    except Exception as e:
        st.error(f"Lỗi rà soát: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ V63")
    if st.button('🚀 CẬP NHẬT DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v63()
    if data is not None and not data.empty:
        st.success(f"✅ Đã lọc: {len(data)} dòng")
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + [int(y) for y in y_list if y > 2000])
        sel_month = st.selectbox("📆 Chọn Tháng", ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)])
        
        df_filtered = data.copy()
        if sel_year != "Tất cả": df_filtered = df_filtered[df_filtered['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả": df_filtered = df_filtered[df_filtered['THÁNG'] == sel_month]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ DASHBOARD TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # CHỈ SỐ
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca (3 Miền)", len(df_filtered))
    c2.metric("Số thiết bị", df_filtered['MÃ_MÁY'].nunique())
    
    heavy_counts = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng >2 lần", len(heavy_counts[heavy_counts > 2]))
    c4.metric("Số Khách hàng", df_filtered['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 BIỂU ĐỒ", "🔍 TRUY LỤC", "🚩 MÁY HỎNG NHIỀU", "🤖 TRỢ LÝ AI", "📖 HƯỚNG DẪN"])

    with tab1:
        st.subheader("🛠️ Top 10 linh kiện lỗi (Dữ liệu 3 Miền)")
        top_err = df_filtered[df_filtered['LÝ_DO'].str.len() > 2]['LÝ_DO'].value_counts().head(10)
        st.bar_chart(top_err)
        
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📍 Tỷ lệ 3 Miền")
            vm_counts = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
            fig_vm = px.pie(vm_counts, values='count', names='VÙNG_MIỀN', hole=0.4)
            st.plotly_chart(fig_vm, use_container_width=True)
        with col_r:
            st.subheader("🏢 Top Khách hàng tiêu biểu")
            kh_counts = df_filtered['KHÁCH_HÀNG'].value_counts().head(10).reset_index()
            fig_kh = px.bar(kh_counts, x='count', y='KHÁCH_HÀNG', orientation='h', color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig_kh, use_container_width=True)

    with tab2:
        q = st.text_input("Gõ mã máy (Toàn lịch sử 3 miền):")
        if q:
            res = data[data['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGÀY', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Danh sách máy hư trên 2 lần")
        list_heavy = heavy_counts[heavy_counts > 2].reset_index()
        list_heavy.columns = ['MÃ_MÁY', 'SỐ_LẦN_HỎNG']
        # Sửa lỗi KeyError bằng cách kiểm tra cột cẩn thận
        info_lookup = data[['MÃ_MÁY', 'KHÁCH_HÀNG', 'VÙNG_MIỀN']].drop_duplicates('MÃ_MÁY')
        merged = pd.merge(list_heavy, info_lookup, on='MÃ_MÁY', how='left')
        st.dataframe(merged, use_container_width=True)

    with tab4:
        st.subheader("🤖 Trợ lý AI")
        st.info("🤖 AI đang trực tuyến. Tôi đã lọc bỏ các dữ liệu ngoài 3 miền Bắc - Trung - Nam cho sếp.")
        ask = st.chat_input("Hỏi về lỗi hoặc khách hàng...")
        if ask:
            st.write(f"💬 **Hỏi:** {ask}")
            if "nhiều nhất" in ask.lower():
                st.write(f"🤖 AI: Theo dữ liệu, đơn vị {df_filtered['KHÁCH_HÀNG'].value_counts().idxmax()} có nhiều ca nhất.")

    with tab5:
        st.markdown("""
        ### 📖 HƯỚNG DẪN V63
        1. **Dữ liệu sạch:** Hệ thống chỉ ghi nhận các dòng có vùng miền là: **Miền Bắc, Miền Trung, Miền Nam**. Các giá trị khác bị loại bỏ.
        2. **Máy hỏng > 2 lần:** Danh sách tự động cập nhật từ toàn bộ 4.000+ dòng dữ liệu gốc.
        3. **Biểu đồ:** Hiện lỗi linh kiện (Bar chart) và tỷ lệ 3 miền (Pie chart).
        """)
else:
    st.warning("⚠️ Không tìm thấy dữ liệu thuộc 3 miền: Bắc, Trung, Nam. Sếp vui lòng kiểm tra lại cột Vùng Miền trong file Sheets.")
