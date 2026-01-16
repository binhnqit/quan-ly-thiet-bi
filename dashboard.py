import streamlit as st
import pandas as pd
import plotly.express as px
import math

# Cấu hình giao diện chuẩn Pro
st.set_page_config(page_title="Quản Trị Tài Sản AI", layout="wide", initial_sidebar_state="expanded")

# Tối ưu CSS để giao diện nhìn sang trọng hơn
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stDataFrame { border-radius: 10px; }
    h1 { color: #1E3A8A; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_vietnam():
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
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ nguyên nhân").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0].str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_vietnam()

# --- SIDEBAR (BẢNG ĐIỀU KHIỂN) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063376.png", width=100)
    st.title("Bảng Điều Khiển")
    
    list_years = sorted(df['NĂM'].unique(), reverse=True)
    selected_year = st.selectbox("📅 Chọn Năm", list_years)
    
    list_months = sorted(df[df['NĂM'] == selected_year]['THÁNG'].unique())
    selected_months = st.multiselect("📆 Chọn Tháng", options=list_months, default=list_months, format_func=lambda x: f"Tháng {x}")
    
    st.divider()
    st.success("Hệ thống đã sẵn sàng")
    st.caption("Phiên bản Enterprise AI v2.5")

# Lọc dữ liệu
df_filtered = df[(df['NĂM'] == selected_year) & (df['THÁNG'].isin(selected_months))]

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI")
st.markdown("---")

# 1. TRỢ LÝ TRUY VẾT AI (Dạng Card)
st.subheader("💬 Trợ lý Tra cứu Hồ sơ")
with st.container():
    c_chat1, c_chat2 = st.columns([1, 5])
    c_chat1.image("https://cdn-icons-png.flaticon.com/512/2040/2040946.png", width=80)
    with c_chat2:
        user_msg = st.text_input("Nhập mã máy để tra cứu bệnh án:", placeholder="Ví dụ: 3534")
        if user_msg:
            import re
            match = re.search(r'\d+', user_msg)
            if match:
                code = str(match.group()).strip()
                full_search = df[df['MÃ_MÁY'] == code]
                if not full_search.empty:
                    st.info(f"🔍 Kết quả tra cứu mã máy **{code}**:")
                    for _, r in full_search.sort_values('NGAY_FIX', ascending=False).iterrows():
                        st.write(f"🔹 **{r['NGAY_FIX'].strftime('%d/%m/%Y')}**: {r['LÝ_DO_HỎNG']} (Vùng: {r['VÙNG_MIỀN']})")
                else:
                    st.error(f"❌ Không tìm thấy dữ liệu cho máy {code}")

st.divider()

# 2. CHỈ SỐ SỨC KHỎE & DỰ BÁO NGÂN SÁCH (Hệ thống KPIs Pro)
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

# Tính toán dự báo cho ngân sách
prices = {"Phím": 450000, "Pin": 850000, "Màn hình": 1500000, "Sạc": 350000, "Nguồn": 1200000}
forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5)
n_months = len(selected_months) if selected_months else 1
total_budget = sum([math.ceil((v / n_months) * 1.2) * prices.get(k, 500000) for k, v in forecast_counts.items()])

col_kpi1.metric("📊 Tổng lượt hỏng kỳ này", f"{len(df_filtered)} ca")
col_kpi2.metric("🔮 Dự phòng ngân sách tháng tới", f"{total_budget:,.0f}đ")
col_kpi3.metric("🚨 Máy cần thanh lý", f"{(df['MÃ_MÁY'].value_counts() >= 4).sum()} thiết bị")

st.divider()

# 3. BẢN ĐỒ DỮ LIỆU & PHÂN TÍCH LỖI
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📍 Phân bổ rủi ro theo vùng")
    fig_pie = px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.6, 
                    color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("🛠️ Top 10 linh kiện lỗi cao")
    reason_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(10).reset_index()
    fig_bar = px.bar(reason_counts, x='count', y='LÝ_DO_HỎNG', orientation='h',
                     color='count', color_continuous_scale='Blues')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_bar, use_container_width=True)

# 4. CHỈ SỐ SỨC KHỎE CHI TIẾT
st.divider()
st.subheader("🌡️ Theo dõi Sức khỏe Hệ thống (Health Monitor)")
health_df = df['MÃ_MÁY'].value_counts().reset_index()
health_df.columns = ['Mã Máy', 'Lượt hỏng']

def apply_status(count):
    if count >= 4: return "🔴 Nguy kịch (Thanh lý)"
    if count == 3: return "🟠 Yếu (Cần bảo trì)"
    return "🟢 Tốt (Ổn định)"

health_df['Trạng thái'] = health_df['Lượt hỏng'].apply(apply_status)
st.table(health_df.head(10))

# 5. MÁY HỎNG BÍ ẨN
st.subheader("🚩 Cảnh báo: Lỗi lạ chưa xác định")
mystery = df[df['LÝ_DO_HỎNG'].str.lower().str.contains('không rõ|chưa xác định|lỗi lạ', na=False)]
if not mystery.empty:
    st.dataframe(mystery[['MÃ_MÁY', 'NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']].tail(10), use_container_width=True)
