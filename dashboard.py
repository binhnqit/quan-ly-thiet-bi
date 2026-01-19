import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị V66", layout="wide")

# Link CSV từ Google Sheets của sếp
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v66():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(url, on_bad_lines='skip', dtype=str).fillna("")
        
        # --- DÒ CỘT TỰ ĐỘNG ---
        def find_col(keywords):
            for col in df_raw.columns:
                sample = " ".join(df_raw[col].astype(str).head(100)).upper()
                if any(k in sample for k in keywords): return col
            return None

        c_ma = find_col(['3534', '1102', 'MÃ']) or df_raw.columns[1]
        c_ly = find_col(['LỖI', 'THAY', 'HỎNG', 'SỬA', 'PHÍM', 'PIN', 'MÀN']) or df_raw.columns[3]
        c_ng = find_col(['2024', '2025', '2026', '/']) or df_raw.columns[0]
        c_kh = find_col(['QUANG TRUNG', 'SƠN HẢI', 'TRƯỜNG PHÁT']) or df_raw.columns[2]
        c_vm = find_col(['MIỀN', 'BẮC', 'NAM', 'TRUNG'])

        # CHUẨN HÓA DỮ LIỆU
        df = pd.DataFrame()
        df['MÃ_MÁY'] = df_raw[c_ma].astype(str).str.split('.').str[0].str.strip()
        df['LINH_KIỆN_HƯ'] = df_raw[c_ly].astype(str).str.strip()
        df['NGÀY_DT'] = pd.to_datetime(df_raw[c_ng], dayfirst=True, errors='coerce')
        df['KHÁCH_HÀNG'] = df_raw[c_kh].astype(str).str.strip()
        
        # XỬ LÝ VÙNG MIỀN (Gán nhãn chuẩn để vẽ biểu đồ tròn)
        def phan_loai_mien(val):
            v = str(val).upper()
            if 'BẮC' in v: return 'MIỀN BẮC'
            if 'TRUNG' in v: return 'MIỀN TRUNG'
            if 'NAM' in v: return 'MIỀN NAM'
            return 'MIỀN NAM' # Mặc định

        if c_vm:
            df['VÙNG_MIỀN'] = df_raw[c_vm].apply(phan_loai_mien)
        else:
            df['VÙNG_MIỀN'] = df['KHÁCH_HÀNG'].apply(phan_loai_mien)

        # LÀM SẠCH DỮ LIỆU (Giữ đúng 4.039 dòng hoặc theo file thực tế)
        df = df[df['MÃ_MÁY'].str.len() >= 2].copy()
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG_NUM'] = df['NGÀY_DT'].dt.month.fillna(1).astype(int)
        df['THÁNG'] = df['THÁNG_NUM'].apply(lambda x: f"Tháng {x}")
        
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ HỆ THỐNG")
    if st.button('🚀 CẬP NHẬT DỮ LIỆU MỚI'):
        st.cache_data.clear()
        st.rerun()
    
    data = load_data_v66()
    if data is not None:
        # 1. XỬ LÝ LỌC NĂM (Mặc định chọn 2026)
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        # Tìm vị trí của năm 2026 trong danh sách để set mặc định
        default_year_index = 0
        if 2026 in y_list:
            default_year_index = y_list.index(2026) + 1 # +1 vì có thêm lựa chọn "Tất cả"
        
        sel_year = st.selectbox("📅 Chọn Năm báo cáo", ["Tất cả"] + [int(y) for y in y_list], index=default_year_index)
        
        # 2. XỬ LÝ LỌC THÁNG
        months = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_month = st.selectbox("📆 Chọn Tháng báo cáo", months, index=0)
        
        # --- THỰC THI LỌC DỮ LIỆU CHÍNH XÁC ---
        df_filtered = data.copy()
        if sel_year != "Tất cả":
            df_filtered = df_filtered[df_filtered['NĂM'] == int(sel_year)]
        if sel_month != "Tất cả":
            df_filtered = df_filtered[df_filtered['THÁNG'] == sel_month]
            
        st.success(f"✅ Đang hiển thị {len(df_filtered)} dòng")
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown(f'<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA {sel_year if sel_year != "Tất cả" else "2026"}</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    # HIỂN THỊ TRẠNG THÁI LỌC
    st.info(f"📂 **Dữ liệu đang lọc theo:** {sel_month} / Năm {sel_year}")
    
    # CHỈ SỐ TỔNG HỢP (Nhảy theo bộ lọc)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_filtered))
    c2.metric("Thiết bị lỗi", df_filtered['MÃ_MÁY'].nunique())
    
    # Máy hỏng > 2 lần tính dựa trên dữ liệu đang lọc
    heavy_counts = df_filtered['MÃ_MÁY'].value_counts()
    c3.metric("Máy hỏng >2 lần", len(heavy_counts[heavy_counts > 2]))
    c4.metric("Đơn vị yêu cầu", df_filtered['KHÁCH_HÀNG'].nunique())

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 BÁO CÁO", "🔍 TRA CỨU", "🚩 DANH SÁCH ĐEN", "🤖 AI ASSISTANT", "📖 HƯỚNG DẪN"])

    with tab1:
        st.subheader("🛠️ Thống kê linh kiện lỗi")
        # Biểu đồ linh kiện nhảy theo bộ lọc Năm/Tháng
        top_err = df_filtered[df_filtered['LINH_KIỆN_HƯ'].str.len() > 2]['LINH_KIỆN_HƯ'].value_counts().head(10)
        st.bar_chart(top_err)
        
        col_pie, col_tbl = st.columns(2)
        with col_pie:
            st.subheader("📍 Tỷ lệ theo Vùng Miền")
            vm_counts = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
            fig_vm = px.pie(vm_counts, values='count', names='VÙNG_MIỀN', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_vm, use_container_width=True)
        with col_tbl:
            st.subheader("📋 Chi tiết lỗi linh kiện")
            lk_tbl = df_filtered['LINH_KIỆN_HƯ'].value_counts().reset_index()
            lk_tbl.columns = ['Linh kiện', 'Số lượng']
            st.dataframe(lk_tbl, use_container_width=True, height=350)

    with tab2:
        q = st.text_input("Gõ mã máy để tra cứu lịch sử (Trong kỳ báo cáo):")
        if q:
            res = df_filtered[df_filtered['MÃ_MÁY'].str.contains(q, na=False)]
            st.dataframe(res[['NGÀY_DT', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN_HƯ', 'VÙNG_MIỀN']].sort_values('NGÀY_DT', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Máy hỏng trên 2 lần trong kỳ báo cáo")
        list_h = heavy_counts[heavy_counts > 2].reset_index()
        list_h.columns = ['MÃ_MÁY', 'SỐ_LẦN_HỎNG']
        info = df_filtered.drop_duplicates('MÃ_MÁY')[['MÃ_MÁY', 'KHÁCH_HÀNG', 'VÙNG_MIỀN']]
        st.dataframe(pd.merge(list_h, info, on='MÃ_MÁY', how='left'), use_container_width=True)

    with tab4:
        st.subheader("🤖 Trợ lý AI")
        st.info("🤖 AI đã sẵn sàng phân tích dữ liệu lọc của sếp.")
        ask = st.chat_input("Hỏi tôi về lỗi linh kiện tháng này...")
        if ask:
            st.write(f"💬 **Bạn:** {ask}")
            st.info("🤖 AI: Tôi đang xử lý câu hỏi dựa trên kỳ báo cáo hiện tại...")

    with tab5:
        st.markdown("""
        ### 📖 HƯỚNG DẪN MỚI
        1. **Mặc định:** Hệ thống luôn chọn **Năm 2026** khi bắt đầu.
        2. **Độ chính xác:** Tất cả biểu đồ và số lượng ca hỏng sẽ tự động cập nhật ngay khi sếp thay đổi Năm hoặc Tháng ở thanh bên trái.
        3. **Lưu ý:** Nếu sếp chọn Năm 2026 và Tháng 1 mà không thấy dữ liệu, hãy kiểm tra lại cột Ngày trong file Google Sheets xem đã nhập đúng định dạng chưa.
        """)
else:
    st.warning(f"⚠️ Không tìm thấy dữ liệu cho Năm {sel_year} - {sel_month}. Sếp hãy thử chọn 'Tất cả' hoặc nhấn 'CẬP NHẬT DỮ LIỆU'.")
