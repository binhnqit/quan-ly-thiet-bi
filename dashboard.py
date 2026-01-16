import streamlit as st
import pandas as pd
import plotly.express as px
import math

st.set_page_config(page_title="Hệ thống Quản trị Laptop AI", layout="wide")

# Link dữ liệu Google Sheets của sếp
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_ai_expert_data():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # 1. Tiền xử lý dữ liệu 
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in text for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa ghi chú").astype(str).str.strip()
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0]
        
        # Xử lý thời gian
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df = df.dropna(subset=['NGAY_FIX'])
        df['YEAR'] = df['NGAY_FIX'].dt.year
        df['MONTH'] = df['NGAY_FIX'].dt.month
        
        # Dọn rác
        df = df[df['MÃ_MÁY'] != 'nan']
        df = df[~df['MÃ_MÁY'].str.contains("STT|MÃ|THEO", na=False)]
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df = load_ai_expert_data()

# --- SIDEBAR: ĐIỀU KHIỂN AI ---
with st.sidebar:
    st.header("🤖 AI Expert Panel")
    list_years = sorted(df['YEAR'].unique(), reverse=True)
    selected_year = st.selectbox("Chọn Năm báo cáo", list_years)
    
    df_year = df[df['YEAR'] == selected_year]
    list_months = sorted(df_year['MONTH'].unique())
    selected_months = st.multiselect("Chọn Tháng phân tích", options=list_months, default=list_months)
    
    st.divider()
    st.info("Chế độ: Dự báo mua sắm thông minh đang bật.")

# Lọc dữ liệu tổng cho Dashboard
mask = (df['YEAR'] == selected_year) & (df['MONTH'].isin(selected_months))
df_filtered = df[mask]

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Enterprise IT Asset Management - AI Driven")

# 1. 💬 AI CHATBOT ASSISTANT
# --- LOGIC CHATBOT NÂNG CẤP (CHUYÊN GIA 15 NĂM) ---
st.subheader("💬 Trợ lý ảo Quản trị thiết bị")
with st.container(border=True):
    col_ai, col_inp = st.columns([1, 4])
    col_ai.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    
    with col_inp:
        user_msg = st.text_input("Tra cứu hồ sơ máy:", placeholder="Ví dụ: 'Máy 3534 hỏng những gì?'", key="chat_input")
        
        if user_msg:
            import re
            # Trích xuất tất cả các số có trong câu hỏi của sếp
            match = re.search(r'\d+', user_msg)
            
            if match:
                code = str(match.group()).strip()
                # Đồng nhất kiểu dữ liệu để truy vấn chính xác 100%
                df['MÃ_MÁY_STR'] = df['MÃ_MÁY'].astype(str).str.strip()
                machine_data = df[df['MÃ_MÁY_STR'] == code]
                
                if not machine_data.empty:
                    num_fixes = len(machine_data)
                    # Lấy danh sách linh kiện/lý do hỏng, loại bỏ trùng lặp
                    reasons = machine_data['LÝ_DO_HỎNG'].unique().tolist()
                    reasons_str = ", ".join(reasons)
                    
                    # Lấy lịch sử theo dòng thời gian
                    history_list = machine_data.sort_values('NGAY_FIX', ascending=False)
                    last_fix = history_list['NGAY_FIX'].iloc[0].strftime('%d/%m/%Y')

                    st.markdown(f"🤖 **AI Trả lời:**")
                    st.success(f"Đã tìm thấy hồ sơ máy **{code}**")
                    
                    # Trình bày dạng danh sách chuyên nghiệp
                    st.write(f"📊 **Thống kê:** Máy đã sửa tổng cộng **{num_fixes} lần**.")
                    st.write(f"🛠️ **Chi tiết hư hỏng:** {reasons_str}")
                    st.write(f"📅 **Cập nhật cuối:** Lần gần nhất sửa vào ngày {last_fix}.")
                    
                    # Đưa ra nhận định chuyên gia
                    if num_fixes >= 3:
                        st.error(f"🚩 **Cảnh báo chuyên gia:** Máy {code} có tỷ lệ hỏng lặp lại cao. Khuyên sếp nên kiểm tra tổng thể hoặc thanh lý để tối ưu chi phí vận hành.")
                    else:
                        st.info(f"✅ **Đánh giá:** Thiết bị vẫn trong ngưỡng vận hành ổn định.")
                else:
                    st.error(f"🤖 **AI Trả lời:** Sếp ơi, mã máy **{code}** chưa có trong dữ liệu hoặc sếp kiểm tra lại mã trên file gốc giúp em ạ!")
            else:
                st.warning("🤖 **AI Trả lời:** Sếp nhập giúp em cái mã số máy (ví dụ: 3534) để em 'lục kho' dữ liệu cho sếp nhé!")
# 2. 🔮 AI INVENTORY FORECAST (Dự báo mua linh kiện) 
st.subheader("🔮 Dự báo mua linh kiện thay thế (30 ngày tới)")
if not df_filtered.empty:
    # Thuật toán dự báo: (Tổng lỗi linh kiện / Số tháng) * 1.2 (Hệ số dự phòng an toàn)
    forecast_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(5).reset_index()
    forecast_counts.columns = ['Linh kiện', 'Thực tế']
    
    n_months = len(selected_months) if len(selected_months) > 0 else 1
    
    cols = st.columns(5)
    for i, row in forecast_counts.iterrows():
        prediction = math.ceil((row['Thực tế'] / n_months) * 1.2)
        cols[i].metric(row['Linh kiện'], f"{prediction} cái", delta=f"Căn cứ {row['Thực tế']} ca lỗi")

st.divider()

# 3. 🔍 TRUY VẾT MÃ MÁY ( DRILL-DOWN)
st.markdown("### 🔍 Truy vết Hồ sơ thiết bị")
search_query = st.text_input("Nhập mã máy (VD: 2498)", key="ai_search").strip()
if search_query:
    history = df[df['MÃ_MÁY'] == search_query].sort_values('NGAY_FIX', ascending=False)
    if not history.empty:
        with st.expander(f"Hồ sơ bệnh án máy {search_query}", expanded=True):
            st.table(history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']])
    else:
        st.error("Không tìm thấy mã máy.")

st.divider()

# 4. BIỂU ĐỒ CHUYÊN SÂU
c1, c2 = st.columns([6, 4])
with c1:
    st.subheader("🛠️ Phân tích lỗi hệ thống (Top 15)")
    reasons = df_filtered['LÝ_DO_HỎNG'].value_counts().head(15).reset_index()
    fig_bar = px.bar(reasons, x='count', y='LÝ_DO_HỎNG', orientation='h', text_auto=True,
                     color='count', color_continuous_scale='Bluered')
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.subheader("📍 Tỷ lệ lỗi theo Vùng")
    vung_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
    fig_pie = px.pie(vung_data, values='count', names='VÙNG_MIỀN', hole=0.5,
                    color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
    st.plotly_chart(fig_pie, use_container_width=True)

# 5. CẢNH BÁO TÀI SẢN (MTBF LOW)
st.subheader("🚨 Cảnh báo: Tài sản hỏng lặp lại cao (>= 3 lần)")
bad_machines = df_filtered['MÃ_MÁY'].value_counts()
bad_machines = bad_machines[bad_machines >= 3].reset_index()
bad_machines.columns = ['Mã Máy', 'Số lần hỏng']
st.dataframe(bad_machines, use_container_width=True)
