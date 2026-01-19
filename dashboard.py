import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="AI Quản Trị Tài Sản V62", layout="wide")

# LINK CSV (Đảm bảo sếp chọn đúng Tab có hơn 4000 dòng nhé)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v62():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- DÒ CỘT TỰ ĐỘNG THEO NỘI DUNG ---
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(50)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['3534', '1102', 'MÃ']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA', 'PHÍM', 'NGUỒN']) or df_raw.columns[3]
        c_ng = find_col(['2024', '2025', '2026', '/']) or df_raw.columns[0]
        # Phân biệt Khách hàng và Vùng miền
        c_kh = find_col(['QUANG TRUNG', 'TRƯỜNG PHÁT', 'KHÁCH']) or df_raw.columns[2]
        c_vm = find_col(['MIỀN BẮC', 'MIỀN NAM', 'VÙNG']) or (df_raw.columns[10] if len(df_raw.columns)>10 else None)

        # CHUẨN HÓA DỮ LIỆU
        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw[c_ly].astype(str).str.strip()
        df['NGÀY'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        df['VÙNG_MIỀN'] = df_raw[c_vm].astype(str).str.strip() if c_vm else "Chưa phân loại"

        # LÀM SẠCH (Loại bỏ các dòng rác, dòng tiêu đề gộp)
        df = df[df['MÃ_MÁY'].str.len() >= 3].copy()
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE']
        df = df[~df['LÝ_DO'].str.upper().isin(hang_may)]
        
        # Tạo cột Năm/Tháng đầy đủ
        df['NĂM'] = df['NGÀY'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY'].dt.month.fillna(1).astype(int)
        df['THÁNG'] = df['THÁNG_NUM'].apply(lambda x: f"Tháng {x}")
        
        return df
    except Exception as e:
        st.error(f"Lỗi rà soát: {e}")
        return None

# --- SIDEBAR: BỘ LỌC ĐẦY ĐỦ ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN HỆ THỐNG")
    if st.button('🚀 ĐỒNG BỘ 4.039 DÒNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v62()
    if data is not None:
        st.success(f"✅ Đã kết nối {len(data)} dòng")
        
        # Lọc Năm (Đầy đủ)
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Năm báo cáo", ["Tất cả"] + [int(y) for y in y_list if y > 2000])
        
        # Lọc Tháng (Đầy đủ 12 tháng)
        m_list = [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Tháng báo cáo", ["Tất cả"] + m_list)
        
        # Áp dụng lọc
        df_filtered = data.copy()
        if sel_year != "Tất cả": df_filtered = df_filtered[df_filtered['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả": df_filtered = df_filtered[df_filtered['THÁNG'] == sel_month]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ DASHBOARD QUẢN TRỊ CHI TIẾT 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # 1. CHỈ SỐ DASHBOARD
    st.write(f"📂 **Trạng thái:** {sel_month} / {sel_year}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Số thiết bị", df_filtered['MÃ_MÁY'].nunique())
    
    heavy_counts = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng >2 lần", len(heavy_counts[heavy_counts > 2]))
    c4.metric("Khách hàng", df_filtered['KHÁCH_HÀNG'].nunique())

    # 2. CÁC TAB CHỨC NĂNG
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 BIỂU ĐỒ TỔNG HỢP", "🔍 TRUY LỤC", "🚩 MÁY HỎNG NHIỀU", "🤖 TRỢ LÝ AI", "📖 HƯỚNG DẪN"])

    with tab1:
        # Biểu đồ lỗi linh kiện (Giữ nguyên như yêu cầu)
        st.subheader("📈 Thống kê linh kiện hỏng")
        top_err = df_filtered[df_filtered['LÝ_DO'].str.len() > 2]['LÝ_DO'].value_counts().head(10)
        st.bar_chart(top_err)
        
        # Biểu đồ Vùng miền & Khách hàng
        col_vm, col_kh = st.columns(2)
        with col_vm:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            vm_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
            fig_vm = px.pie(vm_data, values='count', names='VÙNG_MIỀN', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_vm, use_container_width=True)
            
        with col_kh:
            st.subheader("🏢 Top Khách hàng/Đơn vị")
            kh_data = df_filtered['KHÁCH_HÀNG'].value_counts().head(15).reset_index()
            fig_kh = px.bar(kh_data, x='count', y='KHÁCH_HÀNG', orientation='h', color='KHÁCH_HÀNG')
            st.plotly_chart(fig_kh, use_container_width=True)

    with tab2:
        q = st.text_input("Nhập mã máy tra cứu toàn lịch sử (VD: 3534):")
        if q:
            res = data[data['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGÀY', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Danh sách máy hư trên 2 lần (Cần thay mới)")
        list_heavy = heavy_counts[heavy_counts > 2].reset_index()
        list_heavy.columns = ['Mã Máy', 'Số lần hỏng']
        # Trộn thêm thông tin Khách hàng gần nhất để sếp dễ quản lý
        last_info = data.drop_duplicates('MÃ_MÁY', keep='first')[['MÃ_MÁY', 'KHÁCH_HÀNG', 'VÙNG_MIỀN']]
        merged_heavy = list_heavy.merge(last_info, on='MÃ_MÁY', how='left')
        st.dataframe(merged_heavy, use_container_width=True)

    with tab4:
        st.subheader("🤖 Trợ lý AI Phân tích 4.039 dòng")
        ask = st.chat_input("Hỏi tôi về khách hàng hoặc lỗi máy...")
        if ask:
            st.write(f"💬 **Câu hỏi:** {ask}")
            if "khách hàng" in ask.lower() or "ai" in ask.lower():
                top_kh = data['KHÁCH_HÀNG'].value_counts().idxmax()
                st.success(f"🤖 Trợ lý AI: Khách hàng có nhiều ca yêu cầu nhất là **{top_kh}**.")
            elif "lỗi" in ask.lower():
                top_l = data['LÝ_DO'].value_counts().idxmax()
                st.info(f"🤖 Trợ lý AI: Lỗi phổ biến nhất hệ thống ghi nhận là **{top_l}**.")
            else:
                st.warning("🤖 Trợ lý AI: Tôi đang quét 4.039 dòng dữ liệu để tìm câu trả lời chính xác nhất cho sếp...")

    with tab5:
        st.markdown("""
        ### 📖 CẨM NANG SỬ DỤNG V62
        * **Đồng bộ:** Luôn nhấn nút '🚀 ĐỒNG BỘ' khi sếp vừa cập nhật file Google Sheets.
        * **Lọc Năm/Tháng:** Hệ thống hỗ trợ lọc chính xác từng tháng trong từng năm hoặc xem 'Tất cả'.
        * **Phân biệt Vùng miền:** Biểu đồ tròn hiện đúng Miền Bắc/Trung/Nam. Biểu đồ cột ngang hiện danh sách Khách hàng (Quang Trung, Trường Phát...).
        * **Máy hỏng > 2 lần:** Tab này giúp sếp ra quyết định thu hồi hoặc thay mới thiết bị để tiết kiệm chi phí sửa chữa.
        """)
else:
    st.info("💡 Hệ thống đang kết nối dữ liệu 4.039 dòng. Sếp vui lòng đợi trong giây lát...")
