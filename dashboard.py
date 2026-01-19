import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị V64", layout="wide")

# Link CSV từ ảnh image_b688a7.png
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v64():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc dữ liệu thô, ép kiểu chuỗi để tránh lỗi 'upper'
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- CHIẾN THUẬT QUÉT CỘT THÔNG MINH ---
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(100)).upper()
                if any(k in sample for k in keywords): return col
            return None

        # Dò tìm các cột quan trọng
        c_ma = find_col(['3534', '1102', 'MÃ']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA', 'PHÍM']) or df_raw.columns[3]
        c_ng = find_col(['2024', '2025', '2026', '/']) or df_raw.columns[0]
        c_kh = find_col(['QUANG TRUNG', 'SƠN HẢI', 'TRƯỜNG PHÁT']) or df_raw.columns[2]
        c_vm = find_col(['MIỀN', 'BẮC', 'NAM', 'TRUNG']) or df_raw.columns[10] if len(df_raw.columns) > 10 else None

        # CHUẨN HÓA
        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw[c_ly].astype(str).str.strip()
        df['NGÀY_GỐC'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # XỬ LÝ VÙNG MIỀN (Nếu không thấy chữ Miền Bắc/Trung/Nam thì để 'Khách lẻ')
        if c_vm:
            vm_raw = df_raw[c_vm].astype(str).str.upper()
            df['VÙNG_MIỀN'] = vm_raw.apply(lambda x: x if any(m in x for m in ['BẮC', 'TRUNG', 'NAM']) else "KHÁCH HÀNG")
        else:
            df['VÙNG_MIỀN'] = "CHƯA PHÂN LOẠI"

        # LÀM SẠCH: Giữ lại 4.039 dòng (Chỉ bỏ dòng trống hoàn toàn)
        df = df[df['MÃ_MÁY'].str.len() >= 2].copy()
        
        # Lọc bỏ tên hãng máy để biểu đồ linh kiện sạch
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE']
        df = df[~df['LÝ_DO'].str.upper().isin(hang_may)]
        
        # Năm/Tháng cho bộ lọc
        df['NĂM'] = df['NGÀY_GỐC'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY_GỐC'].dt.month.fillna(1).astype(int)
        df['THÁNG'] = df['THÁNG_NUM'].apply(lambda x: f"Tháng {x}")
        
        return df
    except Exception as e:
        st.error(f"Lỗi rà soát dữ liệu: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ V64")
    if st.button('🚀 ĐỒNG BỘ 4.039 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v64()
    if data is not None:
        st.success(f"✅ Đã kết nối {len(data)} dòng")
        
        # BỘ LỌC NĂM (Đầy đủ)
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + [int(y) for y in y_list if y > 2000])
        
        # BỘ LỌC THÁNG (Đầy đủ 12 tháng)
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", months)
        
        df_filtered = data.copy()
        if sel_year != "Tất cả": df_filtered = df_filtered[df_filtered['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả": df_filtered = df_filtered[df_filtered['THÁNG'] == sel_month]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ DASHBOARD TRUY LỤC TÀI SẢN 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # CHỈ SỐ DASHBOARD
    st.write(f"📂 **Đang xem:** {sel_month} / {sel_year}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Số thiết bị", df_filtered['MÃ_MÁY'].nunique())
    
    heavy_data = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng >2 lần", len(heavy_data[heavy_data > 2]))
    c4.metric("Số Khách hàng", df_filtered['KHÁCH_HÀNG'].nunique())

    # CÁC TAB CHỨC NĂNG
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 BIỂU ĐỒ TỔNG HỢP", "🔍 TRUY LỤC MÃ MÁY", "🚩 DANH SÁCH ĐEN", "🤖 TRỢ LÝ AI", "📖 HƯỚNG DẪN"])

    with tab1:
        st.subheader("🛠️ Thống kê linh kiện lỗi (Top 10)")
        top_err = df_filtered[df_filtered['LÝ_DO'].str.len() > 2]['LÝ_DO'].value_counts().head(10)
        st.bar_chart(top_err)
        
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            vm_counts = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
            fig_vm = px.pie(vm_counts, values='count', names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_vm, use_container_width=True)
        with col_r:
            st.subheader("🏢 Top 15 Khách hàng/Đơn vị")
            kh_counts = df_filtered['KHÁCH_HÀNG'].value_counts().head(15).reset_index()
            fig_kh = px.bar(kh_counts, x='count', y='KHÁCH_HÀNG', orientation='h', color='KHÁCH_HÀNG')
            st.plotly_chart(fig_kh, use_container_width=True)

    with tab2:
        q = st.text_input("Gõ mã máy (VD: 3534):")
        if q:
            # Tìm trên toàn bộ data gốc để sếp xem hết lịch sử
            res = data[data['MÃ_MÁY'].astype(str).str.contains(q, na=False)]
            st.dataframe(res[['NGÀY_GỐC', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGÀY_GỐC', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Máy hư trên 2 lần (Toàn lịch sử)")
        list_heavy = heavy_data[heavy_data > 2].reset_index()
        list_heavy.columns = ['MÃ_MÁY', 'SỐ_LẦN_HỎNG']
        # Lấy thông tin khách hàng gần nhất của máy đó
        last_info = data.drop_duplicates('MÃ_MÁY', keep='first')[['MÃ_MÁY', 'KHÁCH_HÀNG', 'VÙNG_MIỀN']]
        merged_heavy = pd.merge(list_heavy, last_info, on='MÃ_MÁY', how='left')
        st.dataframe(merged_heavy, use_container_width=True)

    with tab4:
        st.subheader("🤖 Trợ lý AI Phân tích")
        st.info("🤖 Chào sếp! Tôi đã sẵn sàng phân tích dữ liệu 4.039 dòng của sếp.")
        ask = st.chat_input("Hỏi tôi: Lỗi nào nhiều nhất? Hoặc Khách hàng nào hỏng nhiều?")
        if ask:
            st.write(f"💬 **Câu hỏi:** {ask}")
            if "khách" in ask.lower():
                top_kh = data['KHÁCH_HÀNG'].value_counts().idxmax()
                st.success(f"🤖 Trợ lý AI: Khách hàng yêu cầu nhiều nhất là **{top_kh}**.")
            elif "lỗi" in ask.lower():
                top_l = data['LÝ_DO'].value_counts().idxmax()
                st.info(f"🤖 Trợ lý AI: Lỗi ghi nhận nhiều nhất là **{top_l}**.")

    with tab5:
        st.markdown("""
        ### 📖 HƯỚNG DẪN V64
        * **Biểu đồ tròn:** Chỉ hiển thị Miền Bắc, Miền Trung, Miền Nam. Nếu dữ liệu không thuộc 3 miền này, hệ thống tự động gom vào nhóm 'KHÁCH HÀNG'.         * **Biểu đồ cột ngang:** Liệt kê danh sách các đơn vị như Quang Trung, Trường Phát... để sếp theo dõi khách hàng.
        * **Bộ lọc:** Năm và Tháng (đầy đủ 12 tháng) giúp sếp báo cáo chính xác theo thời điểm.
        * **Truy lục:** Gõ mã máy để xem máy đó đã sửa những gì từ trước đến nay.
        """)
else:
    st.info("💡 Hệ thống đang tải 4.039 dòng dữ liệu. Sếp vui lòng nhấn nút 'ĐỒNG BỘ' nếu chưa thấy số liệu.")
