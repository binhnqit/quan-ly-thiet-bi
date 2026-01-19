import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 - V61", layout="wide")

# LINK CSV (Sếp nhớ dùng link của đúng TAB chứa 3.651 dòng nhé)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v61():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- DÒ CỘT THÔNG MINH ---
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(100)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['3534', '1102', 'MÃ']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA', 'CÀI']) or df_raw.columns[3]
        c_ng = find_col(['2024', '2025', '2026', '/']) or df_raw.columns[0]
        c_vm = find_col(['MIỀN', 'BẮC', 'NAM', 'TRUNG']) or (df_raw.columns[10] if len(df_raw.columns)>10 else None)

        # CHUẨN HÓA
        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw[c_ly].astype(str).str.strip()
        df['NGÀY'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        if c_vm: df['VÙNG_MIỀN'] = df_raw[c_vm].astype(str).str.strip()
        else: df['VÙNG_MIỀN'] = "Chưa phân loại"

        # LÀM SẠCH
        df = df[df['MÃ_MÁY'].str.len() >= 3].copy()
        hang_may = ['HP', 'DELL', 'ASUS', 'LENOVO', 'ACER', 'APPLE']
        df = df[~df['LÝ_DO'].str.upper().isin(hang_may)]
        
        df['NĂM'] = df['NGÀY'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY'].dt.month.fillna(1).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Lỗi rà soát: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN V61")
    if st.button('🚀 ĐỒNG BỘ DỮ LIỆU TỔNG'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v61()
    if data is not None:
        st.success(f"✅ Kết nối {len(data)} dòng")
        
        # BỘ LỌC NĂM
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + [int(y) for y in y_list])
        
        # BỘ LỌC THÁNG
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng", months)
        
        # THỰC THI LỌC
        df_filtered = data.copy()
        if sel_year != "Tất cả": df_filtered = df_filtered[df_filtered['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            m_num = int(sel_month.split(" ")[1])
            df_filtered = df_filtered[df_filtered['THÁNG'] == m_num]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ QUẢN TRỊ TÀI SẢN CHI TIẾT 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # CHỈ SỐ TỔNG QUÁT
    st.write(f"📂 **Đang hiển thị:** {sel_month} / {sel_year}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Số thiết bị", df_filtered['MÃ_MÁY'].nunique())
    
    heavy_data = data['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng >2 lần", len(heavy_data[heavy_data > 2]))
    c4.metric("Vùng miền", df_filtered['VÙNG_MIỀN'].nunique())

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 BIỂU ĐỒ TỔNG HỢP", "🔍 TRUY LỤC", "🚩 MÁY HỎNG NHIỀU", "🤖 TRỢ LÝ AI", "📖 HƯỚNG DẪN"])

    with tab1:
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("📈 Lỗi linh kiện phổ biến")
            top_err = df_filtered[df_filtered['LÝ_DO'].str.len() > 2]['LÝ_DO'].value_counts().head(10)
            st.bar_chart(top_err)
        
        with col_right:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            vm_counts = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
            fig = px.pie(vm_counts, values='count', names='VÙNG_MIỀN', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        q = st.text_input("Nhập mã máy (VD: 3534):")
        if q:
            res = data[data['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['NGÀY', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGÀY', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Danh sách máy hư trên 2 lần (Toàn thời gian)")
        list_heavy = heavy_data[heavy_data > 2].reset_index()
        list_heavy.columns = ['Mã Máy', 'Số lần hỏng']
        st.table(list_heavy.head(20))

    with tab4:
        st.subheader("🤖 Trợ lý phân tích dữ liệu")
        user_ask = st.chat_input("Hỏi tôi về tình trạng máy móc...")
        if user_ask:
            st.write(f"💬 **Bạn hỏi:** {user_ask}")
            # Logic Trợ lý AI đơn giản (Có thể kết nối API Gemini tại đây)
            if "nhiều nhất" in user_ask.lower():
                top_1 = data['LÝ_DO'].value_counts().idxmax()
                st.info(f"🤖 AI trả lời: Lỗi xuất hiện nhiều nhất là **{top_1}**.")
            else:
                st.info("🤖 AI trả lời: Tôi đã nhận câu hỏi và đang phân tích dữ liệu 3.651 dòng của sếp...")

    with tab5:
        st.markdown("""
        ### 📖 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG
        1. **Đồng bộ dữ liệu:** Nhấn nút '🚀 ĐỒNG BỘ' ở Sidebar để lấy dữ liệu mới nhất từ Google Sheets.
        2. **Lọc dữ liệu:** Sử dụng dropdown Năm và Tháng để xem báo cáo cụ thể.
        3. **Truy lục:** Vào Tab 'TRUY LỤC', nhập mã máy để xem toàn bộ lịch sử sửa chữa từ trước tới nay.
        4. **Máy hỏng nhiều:** Theo dõi Tab này để có kế hoạch thanh lý hoặc thay mới thiết bị kém chất lượng.
        5. **Lưu ý:** Để dữ liệu chính xác, hãy đảm bảo file Google Sheets nhập đúng cột Ngày và Mã máy.
        """)
else:
    st.info("💡 Đang tải dữ liệu... Sếp hãy kiểm tra Link CSV hoặc nhấn 'LÀM MỚI'.")
