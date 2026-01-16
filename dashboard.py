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
# --- NÂNG CẤP CHATBOT TÌM KIẾM TOÀN DIỆN ---
st.subheader("💬 Trợ lý ảo AI - Truy lục hồ sơ tổng")
with st.container(border=True):
    col_ai, col_inp = st.columns([1, 4])
    col_ai.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    
    with col_inp:
        user_msg = st.text_input("Tra cứu hồ sơ máy (Quét toàn hệ thống):", 
                                 placeholder="Nhập mã máy cần tra cứu...", key="final_search")
        
        if user_msg:
            import re
            # Lấy số từ câu hỏi
            match = re.search(r'\d+', user_msg)
            
            if match:
                target_code = str(match.group()).strip()
                
                # BƯỚC QUAN TRỌNG: Quét trên 'df' gốc, KHÔNG quét trên 'df_filtered'
                # Dùng str.contains để tìm kiếm linh hoạt hơn
                full_search = df[df['MÃ_MÁY'].astype(str).str.contains(target_code, na=False)]
                
                if not full_search.empty:
                    st.markdown(f"🤖 **AI Trả lời:** Đã lục tìm thấy **{len(full_search)} lần** sửa chữa cho máy có chứa số **{target_code}**:")
                    
                    # Liệt kê chi tiết thực tế
                    for i, row in full_search.sort_values('NGAY_FIX', ascending=False).iterrows():
                        ngay = row['NGAY_FIX'].strftime('%d/%m/%Y')
                        loi = row['LÝ_DO_HỎNG']
                        vung = row['VÙNG_MIỀN']
                        st.write(f"📍 Ngày **{ngay}**: Hỏng **{loi}** (Khu vực: {vung})")
                    
                    if len(full_search) >= 3:
                        st.error("⚠️ **Cảnh báo chuyên gia:** Tần suất hỏng quá cao, máy này đang 'đốt tiền' của sếp đấy!")
                else:
                    st.error(f"🤖 AI Trả lời: Không tìm thấy mã {target_code} trong toàn bộ 4.000 dòng. Sếp kiểm tra lại mã trên file gốc nhé!")
            else:
                st.info("🤖 AI Trả lời: Sếp nhập mã máy để em kiểm tra ngay ạ.")
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
# --- BẢNG PHÂN TÍCH MÁY HỎNG BÍ ẨN ---
st.divider()
st.subheader("🚩 Top 10 Máy hỏng bí ẩn (Cần kiểm tra chuyên sâu)")

# Định nghĩa các từ khóa "bí ẩn" thường gặp trong dữ liệu
mystery_keywords = ['không rõ', 'chưa xác định', 'lỗi lạ', 'kiểm tra', 'theo dõi', 'hỏng chưa rõ']

# Lọc các máy có lý do hỏng chứa từ khóa bí ẩn
df_mystery = df[df['LÝ_DO_HỎNG'].str.lower().str.contains('|'.join(mystery_keywords), na=False)]

if not df_mystery.empty:
    # Đếm số lần hỏng của những máy này
    mystery_counts = df_mystery['MÃ_MÁY'].value_counts().reset_index()
    mystery_counts.columns = ['Mã Máy', 'Số lần hỏng "bí ẩn"']
    
    # Lấy Top 10
    top_10_mystery = mystery_counts.head(10)
    
    # Hiển thị bảng kèm chú thích chuyên gia
    col_tab, col_note = st.columns([7, 3])
    
    with col_tab:
        st.dataframe(top_10_mystery, use_container_width=True)
        
    with col_note:
        st.info("""
        **💡 Khuyến nghị của AI:**
        Các máy trong danh sách này đang có 'bệnh lý' không rõ ràng nhưng lặp lại. 
        - Sếp nên yêu cầu kỹ thuật viên lập biên bản kiểm tra tổng thể.
        - Ưu tiên thay thế linh kiện thay vì sửa vá để tránh gián đoạn công việc.
        """)
else:
    st.success("✅ Tuyệt vời sếp ơi! Hiện chưa ghi nhận máy nào có lỗi 'bí ẩn' trong kỳ này.")
# --- TÍNH NĂNG CHẤM ĐIỂM SỨC KHỎE THIẾT BỊ ---
st.divider()
st.header("🌡️ Asset Health Monitor (Chấm điểm sức khỏe)")

def calculate_health(row_count):
    if row_count >= 4: return "🔴 Nguy kịch (Dưới 30đ)", "Thanh lý ngay"
    if row_count == 3: return "🟠 Yếu (50đ)", "Cần bảo trì tổng thể"
    if row_count == 2: return "🟡 Tạm ổn (75đ)", "Theo dõi thêm"
    return "🟢 Tốt (95đ)", "Vận hành bình thường"

# Lấy danh sách máy và tính điểm
health_df = df['MÃ_MÁY'].value_counts().reset_index()
health_df.columns = ['Mã Máy', 'Lượt hỏng']
health_df[['Trạng thái', 'Khuyến nghị']] = health_df['Lượt hỏng'].apply(lambda x: pd.Series(calculate_health(x)))

# Hiển thị Top máy cần chú ý nhất
st.write("📋 **Danh sách thiết bị cần ưu tiên xử lý:**")
st.dataframe(health_df.head(10).style.applymap(
    lambda x: 'color: red; font-weight: bold' if 'Nguy kịch' in str(x) else '', subset=['Trạng thái']
), use_container_width=True)

# --- BIỂU ĐỒ DỰ BÁO TÀI CHÍNH (GIẢ LẬP) ---
st.subheader("💰 Ước tính ngân sách linh kiện (Dựa trên dự báo AI)")
# Giả sử giá trung bình linh kiện là 500k
avg_cost = 500000 
forecast_data['Chi phí dự kiến (VNĐ)'] = forecast_data['Dự báo cần mua'] * avg_cost

fig_cost = px.pie(forecast_data, values='Chi phí dự kiến (VNĐ)', names='Linh kiện', 
                 title="Phân bổ ngân sách dự phòng tháng tới",
                 color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(fig_cost, use_container_width=True)
