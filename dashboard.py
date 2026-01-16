import streamlit as st
import pandas as pd
import plotly.express as px
import math

st.set_page_config(page_title="Hệ thống Quản trị Laptop AI", layout="wide")

PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_ai_data():
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
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0]
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        
        df = df.dropna(subset=['NGAY_FIX'])
        df['YEAR'] = df['NGAY_FIX'].dt.year
        df['MONTH'] = df['NGAY_FIX'].dt.month
        
        # Bổ sung cột Chi phí dự kiến để AI học (Giả lập để sếp nhập sau)
        df['MODEL'] = "Standard Business" # Sếp có thể thay bằng cột thực tế
        
        df = df[df['MÃ_MÁY'] != 'nan']
        df = df[~df['MÃ_MÁY'].str.contains("STT|MÃ|THEO", na=False)]
        return df
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame()

df = load_ai_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🤖 AI Control Center")
    list_years = sorted(df['YEAR'].unique(), reverse=True)
    selected_year = st.selectbox("Chọn Năm báo cáo", list_years)
    
    df_year = df[df['YEAR'] == selected_year]
    list_months = sorted(df_year['MONTH'].unique())
    selected_months = st.multiselect("Chọn Tháng", options=list_months, default=list_months)
    
    st.divider()
    st.info("💡 Chatbot AI đang ở chế độ chờ tích hợp (LLM Ready)")

# Lọc dữ liệu
mask = (df['YEAR'] == selected_year) & (df['MONTH'].isin(selected_months))
df_filtered = df[mask]

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Enterprise IT Asset Management - AI Driven")

# 1. AI CHATBOT INTERFACE (MÔ PHỎNG)
with st.expander("💬 Chat với Trợ lý ảo AI (Hỏi về linh kiện, máy lỗi...)", expanded=False):
    st.write("Chào sếp! Tôi đã học xong 4.000 dòng dữ liệu. Sếp cần tra cứu gì ạ?")
    user_msg = st.text_input("Gõ câu hỏi tại đây...", placeholder="Ví dụ: Cần mua bao nhiêu phím cho tháng tới?")
    if user_msg:
        st.write("🤖 **AI Trả lời:** Hệ thống đang phân tích xu hướng... (Đây là khung chờ kết nối GPT/Gemini API)")

# 2. DỰ BÁO MUA LINH KIỆN (AI FORECASTING)
st.subheader("🔮 Dự báo nhu cầu linh kiện (30 ngày tới)")
if not df_filtered.empty:
    # Thuật toán: Lấy trung bình số ca hỏng mỗi tháng trong kỳ lọc và cộng thêm 15% hệ số an toàn
    forecast_data = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5).reset_index()
    forecast_data.columns = ['Linh kiện', 'Số ca hỏng thực tế']
    
    num_months = len(selected_months) if len(selected_months) > 0 else 1
    forecast_data['Dự báo cần mua'] = forecast_data['Số ca hỏng thực tế'].apply(lambda x: math.ceil((x / num_months) * 1.15))
    
    cols = st.columns(len(forecast_data))
    for i, row in forecast_data.iterrows():
        cols[i].metric(row['Linh kiện'], f"+{row['Dự báo cần mua']} cái", delta="Dự trù kho")

st.divider()

# 3. TRUY VẾT MÃ MÁY ĐỘC LẬP
st.markdown("### 🔍 Truy vết Hồ sơ thiết bị")
search_query = st.text_input("Nhập mã máy (VD: 2498)", key="ai_search").strip()
if search_query:
    history = df[df['MÃ_MÁY'] == search_query].sort_values('NGAY_FIX', ascending=False)
    if not history.empty:
        with st.container(border=True):
            st.info(f"📋 **HỒ SƠ: {search_query}**")
            st.table(history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
    else:
        st.error("Không tìm thấy mã máy.")

st.divider()

# 4. BIỂU ĐỒ CHUYÊN GIA
col_a, col_b = st.columns([6, 4])
with col_a:
    st.subheader("🛠️ Phân tích lỗi theo mô hình AI (Top 15)")
    reasons = df_filtered['LÝ_DO_HỎNG'].value_counts().head(15).reset_index()
    fig_bar = px.bar(reasons, x='count', y='LÝ_DO_HỎNG', orientation='h', text_auto=True,
                     color='count', color_continuous_scale='Magma')
    st.plotly_chart(fig_bar, use_container_width=True)

with col_b:
    st.subheader("📍 Tỷ lệ lỗi theo Vùng")
    vung_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
    fig_pie = px.pie(vung_data, values='count', names='VÙNG_MIỀN', hole=0.5,
                    color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
    st.plotly_chart(fig_pie, use_container_width=True)
