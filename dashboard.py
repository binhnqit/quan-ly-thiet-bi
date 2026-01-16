import streamlit as st
import pandas as pd
import plotly.express as px
import math

# 1. CẤU HÌNH GIAO DIỆN PRO
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

# CSS tạo phong cách doanh nghiệp chuyên nghiệp
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 4px solid #1E3A8A; }
    .guide-box { background-color: #ffffff; padding: 25px; border-radius: 12px; border-left: 6px solid #1E3A8A; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #1E3A8A; font-weight: 800; text-align: center; margin-bottom: 30px; }
    h3 { color: #1E3A8A; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU TỪ GOOGLE SHEETS
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_final():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # Tiền xử lý dữ liệu vùng miền
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác"

        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0].str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame()

df = load_data_final()

# --- SIDEBAR: BỘ LỌC CHIẾN LƯỢC ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063376.png", width=80)
    st.title("🛡️ BỘ LỌC AI")
    
    if not df.empty:
        list_years = sorted(df['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Năm báo cáo", list_years)
        
        list_vung = sorted(df['VÙNG_MIỀN'].unique())
        sel_vung = st.multiselect("📍 Khu vực (Vùng)", list_vung, default=list_vung)
        
        df_temp = df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))]
        list_months = sorted(df_temp['THÁNG'].unique())
        sel_months = st.multiselect("📆 Tháng phân tích", list_months, default=list_months, format_func=lambda x: f"Tháng {x}")
        
        st.divider()
        # Xuất dữ liệu CSV
        csv_data = df_temp.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📄 Tải Báo Cáo (Excel/CSV)", data=csv_data, file_name=f'Bao_cao_{sel_year}.csv', mime='text/csv')

# --- LOGIC LỌC DỮ LIỆU ---
if not df.empty:
    df_filtered = df[(df['NĂM'] == sel_year) & 
                     (df['THÁNG'].isin(sel_months)) & 
                     (df['VÙNG_MIỀN'].isin(sel_vung))]
else:
    df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
tab1, tab2 = st.tabs(["📊 BÁO CÁO CHIẾN LƯỢC", "📖 HƯỚNG DẪN VẬN HÀNH"])

with tab1:
    st.title("🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI")
    
    # 1. KPI TỔNG QUAN
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Tổng lượt hỏng kỳ này", f"{len(df_filtered)} ca")
    
    # Dự báo ngân sách
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    n_m = len(sel_months) if sel_months else 1
    est_budget = sum([math.ceil((v/n_m)*1.2)*500000 for v in forecast_counts.values])
    col_kpi2.metric("Ngân sách dự phòng", f"{est_budget:,.0f}đ")
    
    # Thiết bị đỏ (Toàn hệ thống)
    bad_assets = (df['MÃ_MÁY'].value_counts() >= 4).sum()
    col_kpi3.metric("Máy nguy kịch (Đỏ)", f"{bad_assets} máy")

    st.divider()

    # 2. TRỢ LÝ AI (TRA CỨU TOÀN DIỆN)
    st.subheader("💬 Trợ lý Tra cứu Hồ sơ Bệnh án")
    with st.container():
        user_msg = st.text_input("Gõ mã máy để AI truy lục lịch sử (VD: 3534):", placeholder="Mã máy...")
        if user_msg:
            import re
            m = re.search(r'\d+', user_msg)
            if m:
                code = m.group()
                history = df[df['MÃ_MÁY'] == code].sort_values('NGAY_FIX', ascending=False)
                if not history.empty:
                    st.info(f"🔍 Kết quả cho máy **{code}**: {len(history)} lần ghi nhận.")
                    st.dataframe(history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']], use_container_width=True)
                else:
                    st.error(f"❌ Không tìm thấy mã máy {code} trong hệ thống.")

    st.divider()

    # 3. BIỂU ĐỒ PHÂN TÍCH
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📍 Tỷ lệ hỏng theo Vùng")
        if not df_filtered.empty:
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
    with col_r:
        st.subheader("🛠️ Top 10 lỗi phổ biến nhất")
        if not df_filtered.empty:
            st.plotly_chart(px.bar(df_filtered['LÝ_DO_HỎNG'].value_counts().head(10), orientation='h', color_discrete_sequence=['#1E3A8A']), use_container_width=True)

    # 4. DANH SÁCH SỨC KHỎE
    st.subheader("🌡️ Chỉ số sức khỏe thiết bị (Health Score)")
    health = df['MÃ_MÁY'].value_counts().reset_index()
    health.columns = ['Mã Máy', 'Lượt hỏng']
    health['Trạng thái'] = health['Lượt hỏng'].apply(lambda x: "🔴 Nguy kịch" if x>=4 else ("🟠 Yếu" if x==3 else "🟢 Tốt"))
    st.dataframe(health.head(20), use_container_width=True)
  # --- PHẦN TỐI ƯU DỰ BÁO CHI PHÍ ---
    st.divider()
    st.subheader("💰 Kế hoạch Ngân sách & Dự báo Tài chính (Tháng tới)")
    
    # 1. Định nghĩa bảng giá linh kiện thực tế (Sếp có thể điều chỉnh số liệu ở đây)
    pricing_dict = {
        "Phím": 450000,
        "Pin": 950000,
        "Màn hình": 1800000,
        "Sạc": 350000,
        "Nguồn": 1200000,
        "Ổ cứng": 1100000,
        "Vệ sinh": 150000,
        "Chưa rõ": 500000 # Chi phí dự phòng cho lỗi lạ
    }

    if not df_filtered.empty:
        # 2. Tính toán tần suất hỏng theo loại linh kiện
        def get_main_component(reason):
            for k in pricing_dict.keys():
                if k.lower() in reason.lower(): return k
            return "Chưa rõ"

        df_filtered['LINH_KIỆN'] = df_filtered['LÝ_DO_HỎNG'].apply(get_main_component)
        comp_stats = df_filtered['LINH_KIỆN'].value_counts().reset_index()
        comp_stats.columns = ['Linh kiện', 'Số ca kỳ này']

        # 3. Thuật toán dự báo: (Trung bình tháng * Hệ số tăng trưởng 1.2)
        n_months_act = len(sel_months) if sel_months else 1
        comp_stats['Dự báo tháng tới'] = comp_stats['Số ca kỳ này'].apply(lambda x: math.ceil((x/n_m)*1.2))
        comp_stats['Đơn giá (đ)'] = comp_stats['Linh kiện'].map(pricing_dict)
        comp_stats['Thành tiền (đ)'] = comp_stats['Dự báo tháng tới'] * comp_stats['Đơn giá (đ)']

        # Hiển thị số liệu tổng quát
        total_est = comp_stats['Thành tiền (đ)'].sum()
        
        c_fin1, c_fin2 = st.columns([6, 4])
        with c_fin1:
            st.write("**Bảng kê dự toán mua sắm linh kiện:**")
            st.dataframe(comp_stats[['Linh kiện', 'Dự báo tháng tới', 'Thành tiền (đ)']], use_container_width=True)
            st.warning(f"💡 **Tổng ngân sách đề xuất cho {len(sel_vung)} miền:** {total_est:,.0f} VNĐ")
        
        with c_fin2:
            fig_budget = px.pie(comp_stats, values='Thành tiền (đ)', names='Linh kiện', 
                               title="Cơ cấu chi phí theo linh kiện",
                               hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_budget, use_container_width=True)

    st.divider()
with tab2:
    st.markdown("""
    <div class="guide-box">
        <h3>📖 HƯỚNG DẪN VẬN HÀNH CHO NHÂN VIÊN</h3>
        <ul>
            <li><b>1. Nhập liệu chuẩn:</b> Nhập đúng số máy (Cột A) và lý do (Cột D) trên Google Sheets.</li>
            <li><b>2. Tra cứu nhanh:</b> Luôn dùng Trợ lý AI để kiểm tra trước khi cấp phát linh kiện mới.</li>
            <li><b>3. Quản lý vùng:</b> Sử dụng bộ lọc Sidebar bên trái để xem dữ liệu theo chi nhánh/miền.</li>
            <li><b>4. Xuất báo cáo:</b> Dùng nút "Tải Báo Cáo" ở Sidebar hoặc nhấn <b>Ctrl + P</b> để lưu Dashboard sang PDF.</li>
        </ul>
        <p><i>Hệ thống được vận hành bởi AI Expert v5.1</i></p>
    </div>
    """, unsafe_allow_html=True)
  
