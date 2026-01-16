import streamlit as st
import pandas as pd
import plotly.express as px
import math

st.set_page_config(page_title="Hệ thống Quản trị Laptop AI", layout="wide")

# 1. KẾT NỐI DỮ LIỆU
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_pro():
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
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa ghi chú").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0].str.strip()
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['YEAR'] = df['NGAY_FIX'].dt.year
        df['MONTH'] = df['NGAY_FIX'].dt.month
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_pro()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🤖 AI Control Center")
    list_years = sorted(df['YEAR'].unique(), reverse=True)
    selected_year = st.selectbox("Chọn Năm báo cáo", list_years)
    list_months = sorted(df[df['YEAR'] == selected_year]['MONTH'].unique())
    selected_months = st.multiselect("Chọn Tháng", options=list_months, default=list_months)
    st.divider()
    st.info("Chế độ: Expert ERP v2.0")

# Lọc dữ liệu cho Dashboard
df_filtered = df[(df['YEAR'] == selected_year) & (df['MONTH'].isin(selected_months))]

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Enterprise Asset Intelligence Dashboard")

# 1. CHATBOT AI (QUÉT TOÀN BỘ DATA)
with st.container(border=True):
    col_ai, col_inp = st.columns([1, 4])
    col_ai.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    with col_inp:
        user_msg = st.text_input("💬 Chat với Trợ lý AI (Tra cứu bệnh án máy):", placeholder="Ví dụ: 'Máy 3534 hỏng gì?'")
        if user_msg:
            import re
            match = re.search(r'\d+', user_msg)
            if match:
                code = str(match.group()).strip()
                full_search = df[df['MÃ_MÁY'] == code]
                if not full_search.empty:
                    st.write(f"🤖 **Hồ sơ máy {code}:** {len(full_search)} lần hỏng.")
                    for _, r in full_search.sort_values('NGAY_FIX', ascending=False).iterrows():
                        st.write(f"- {r['NGAY_FIX'].strftime('%d/%m/%Y')}: {r['LÝ_DO_HỎNG']} ({r['VÙNG_MIỀN']})")
                else:
                    st.error(f"Không tìm thấy mã {code}")

st.divider()

# 2. DỰ BÁO LINH KIỆN & NGÂN SÁCH
st.subheader("🔮 Dự báo mua sắm & Ngân sách (Tháng tới)")
if not df_filtered.empty:
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5).reset_index()
    forecast_counts.columns = ['Linh kiện', 'Số ca']
    n_months = len(selected_months) if selected_months else 1
    
    # Giá linh kiện giả lập (Sếp có thể sửa ở đây)
    prices = {"Phím": 450000, "Pin": 850000, "Màn hình": 1500000, "Sạc": 300000, "Main": 2500000}
    
    c1, c2, c3, c4, c5 = st.columns(5)
    cols = [c1, c2, c3, c4, c5]
    
    total_budget = 0
    for i, row in forecast_counts.iterrows():
        prediction = math.ceil((row['Số ca'] / n_months) * 1.2)
        price = prices.get(row['Linh kiện'], 500000)
        total_budget += prediction * price
        if i < 5:
            cols[i].metric(row['Linh kiện'], f"+{prediction} cái", f"{prediction * price:,.0f}đ")
    
    st.info(f"💰 **Tổng ngân sách dự trù cho tháng tới:** {total_budget:,.0f} VNĐ")

st.divider()

# 3. CHẤM ĐIỂM SỨC KHỎE (HEALTH SCORE)
st.subheader("🌡️ Chỉ số sức khỏe thiết bị (Health Score)")
health_counts = df['MÃ_MÁY'].value_counts().reset_index()
health_counts.columns = ['Mã Máy', 'Lượt hỏng']

def get_health(count):
    if count >= 4: return "🔴 Nguy kịch", "Thanh lý ngay"
    if count == 3: return "🟠 Yếu", "Bảo trì tổng thể"
    return "🟢 Tốt", "Vận hành ổn định"

health_counts[['Trạng thái', 'Khuyến nghị']] = health_counts['Lượt hỏng'].apply(lambda x: pd.Series(get_health(x)))
st.dataframe(health_counts.head(10), use_container_width=True)

# 4. TOP MÁY BÍ ẨN
st.subheader("🚩 Top Máy hỏng bí ẩn (Cần kiểm tra kỹ thuật)")
mystery_list = df[df['LÝ_DO_HỎNG'].str.lower().str.contains('không rõ|chưa xác định|lỗi lạ|kiểm tra', na=False)]
if not mystery_list.empty:
    st.dataframe(mystery_list['MÃ_MÁY'].value_counts().head(5), use_container_width=True)

# 5. BIỂU ĐỒ TỔNG QUAN
st.divider()
col_l, col_r = st.columns(2)
with col_l:
    st.subheader("📊 Tỷ lệ lỗi theo Vùng")
    st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', hole=0.5, color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"}), use_container_width=True)
with col_r:
    st.subheader("🛠️ Top 10 lỗi phổ biến")
    st.plotly_chart(px.bar(df_filtered['LÝ_DO_HỎNG'].value_counts().head(10), orientation='h'), use_container_width=True)
