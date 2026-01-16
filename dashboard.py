import streamlit as st
import pandas as pd
import plotly.express as px
import math
from fpdf import FPDF
import base64

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #1E3A8A; text-align: center; }
    .guide-box { background-color: #e1f5fe; padding: 20px; border-radius: 10px; border-left: 5px solid #01579b; }
    </style>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI DỮ LIỆU
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_final():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"
        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).split('.').str[0].str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except: return pd.DataFrame()

df = load_data_final()

# --- TABS: DASHBOARD & HƯỚNG DẪN ---
tab_main, tab_guide = st.tabs(["📊 Bảng Điều Khiển Chiến Lược", "📖 Hướng Dẫn Sử Dụng"])

with tab_main:
    st.title("🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI")
    
    # Sidebar Filters
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        selected_year = st.selectbox("Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_year = df[df['NĂM'] == selected_year]
        selected_months = st.multiselect("Chọn Tháng", sorted(df_year['THÁNG'].unique()), default=sorted(df_year['THÁNG'].unique()))
        
        st.divider()
        # NÚT XUẤT BÁO CÁO PDF
        if st.button("📄 Xuất Báo Cáo PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="BAO CAO QUAN TRI TAI SAN AI", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Nam bao cao: {selected_year}", ln=True, align='L')
            pdf.cell(200, 10, txt=f"Tong so ca hỏng: {len(df_year)}", ln=True, align='L')
            pdf_output = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_output).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="Bao_cao_AI_{selected_year}.pdf">Nhấn vào đây để tải PDF</a>'
            st.markdown(href, unsafe_allow_html=True)

    # Lọc dữ liệu hiển thị
    df_filtered = df[(df['NĂM'] == selected_year) & (df['THÁNG'].isin(selected_months))]

    # KPI Row
    c1, c2, c3 = st.columns(3)
    c1.metric("Lượt hỏng kỳ này", f"{len(df_filtered)} ca")
    
    # Tính dự báo ngân sách
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
    budget = sum([math.ceil((v/len(selected_months))*1.2)*500000 for k,v in forecast_counts.items()]) if selected_months else 0
    c2.metric("Dự phòng ngân sách", f"{budget:,.0f}đ")
    c3.metric("Thiết bị đỏ (Health < 30)", f"{(df['MÃ_MÁY'].value_counts() >= 4).sum()}")

    # Chatbot & Biểu đồ (như cũ)
    st.divider()
    # ... (Các phần biểu đồ và chatbot giữ nguyên từ bản trước) ...

with tab_guide:
    st.header("📖 Hướng Dẫn Vận Hành Hệ Thống")
    st.markdown("""
    <div class="guide-box">
        <h4>1. Quy trình nhập liệu chuẩn (Google Sheets)</h4>
        <ul>
            <li><b>Cột Mã Máy:</b> Chỉ nhập số (Ví dụ: 3534). Tránh nhập kèm chữ.</li>
            <li><b>Cột Lý do hỏng:</b> Nhập rõ ràng (Ví dụ: "Lỗi Pin", "Liệt Phím"). Nếu chưa rõ bệnh, nhập "Lỗi lạ - Đang kiểm tra".</li>
            <li><b>Cột Ngày sửa:</b> Định dạng chuẩn Ngày/Tháng/Năm.</li>
        </ul>
        
        <h4>2. Cách sử dụng Trợ lý AI</h4>
        <ul>
            <li>Gõ trực tiếp mã số máy vào ô tìm kiếm để xem "Bệnh án trọn đời".</li>
            <li>AI sẽ tự động cảnh báo <b>Màu đỏ</b> nếu máy đó đã sửa quá 4 lần.</li>
        </ul>

        <h4>3. Ý nghĩa các chỉ số</h4>
        <ul>
            <li><b>Health Score:</b> 🟢 Tốt (1-2 lần sửa), 🟠 Yếu (3 lần), 🔴 Nguy kịch (>=4 lần).</li>
            <li><b>Dự phòng ngân sách:</b> AI tính dựa trên lịch sử lỗi thực tế + 20% hệ số rủi ro phát sinh.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
