import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Thiết bị Pro", layout="wide")

# Link ID từ Google Sheets
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data_full():
    try:
        # Đọc dữ liệu (bỏ qua dòng tiêu đề gộp ô đầu tiên)
        df = pd.read_csv(URL, header=1)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Mapping cột (Tương thích với tên cột trong hình sếp gửi)
        mapping = {
            'MÃ SỐ MÁY': next((c for c in df.columns if "MÁY" in c), None),
            'KHU VỰC': next((c for c in df.columns if "KHU VỰC" in c or "CHI NHÁNH" in c), None),
            'TÌNH TRẠNG': next((c for c in df.columns if "TRẠNG" in c or "KIỂM TRA" in c), None),
            'SỬA NỘI BỘ': next((c for c in df.columns if "NỘI BỘ" in c), None),
            'SỬA BÊN NGOÀI': next((c for c in df.columns if "NGOÀI" in c), None)
        }

        if mapping['MÃ SỐ MÁY']:
            df = df.dropna(subset=[mapping['MÃ SỐ MÁY']])
            df['Mã số máy'] = df[mapping['MÃ SỐ MÁY']].astype(str).str.split('.').str[0].str.strip()
            df['Khu vực'] = df[mapping['KHU VỰC']] if mapping['KHU VỰC'] else "N/A"
            df['Tình trạng'] = df[mapping['TÌNH TRẠNG']] if mapping['TÌNH TRẠNG'] else "N/A"
            
            # Xử lý chi phí (ép về kiểu số)
            for col in [mapping['SỬA NỘI BỘ'], mapping['SỬA BÊN NGOÀI']]:
                if col:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            df['Tổng chi phí'] = df[mapping['SỬA NỘI BỘ']] + df[mapping['SỬA BÊN NGOÀI']]
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

df_raw = load_data_full()

# --- SIDEBAR: BỘ LỌC ---
st.sidebar.header("🔍 BỘ LỌC DỮ LIỆU")
if not df_raw.empty:
    all_areas = ["Tất cả"] + sorted(df_raw['Khu vực'].unique().tolist())
    selected_area = st.sidebar.selectbox("Chọn Khu vực", all_areas)
    
    search_id = st.sidebar.text_input("Tìm Mã số máy (VD: 355)")

    # Áp dụng lọc
    df = df_raw.copy()
    if selected_area != "Tất cả":
        df = df[df['Khu vực'] == selected_area]
    if search_id:
        df = df[df['Mã số máy'].str.contains(search_id)]

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df_raw.empty:
    # 1. Thống kê nhanh (KPIs)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng lượt lỗi", len(df))
    c2.metric("Tổng chi phí", f"{df['Tổng chi phí'].sum():,.0f}")
    
    counts = df['Mã số máy'].value_counts()
    bad_devices = counts[counts >= 2]
    c3.metric("Máy hỏng ≥ 2 lần", len(bad_devices), delta="Cảnh báo thanh lý", delta_color="inverse")
    c4.metric("Khu vực đang lọc", selected_area)

    st.divider()

    # 2. Phân tích chi phí & Xu hướng
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("💰 Chi phí theo Khu vực")
        cost_chart = df.groupby('Khu vực')['Tổng chi phí'].sum().reset_index()
        cost_chart.columns = ['Khu vực', 'VNĐ']
        fig_cost = px.bar(cost_chart, x='Khu vực', y='VNĐ', color='Khu vực', text_auto='.2s')
        st.plotly_chart(fig_cost, use_container_width=True)

    with col_right:
        st.subheader("🧩 Cơ cấu loại hư hỏng")
        reason_chart = df['Tình trạng'].value_counts().reset_index()
        reason_chart.columns = ['Lý do', 'Số lượng']
        fig_pie = px.pie(reason_chart, names='Lý do', values='Số lượng', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # 3. AI Phân tích: Danh sách máy "Đen"
    st.subheader("🚨 DANH SÁCH MÁY CÓ NGUY CƠ CAO (BLACKLIST)")
    if not bad_devices.empty:
        # Lấy thông tin chi tiết của các máy hỏng nhiều lần
        df_blacklist = df[df['Mã số máy'].isin(bad_devices.index)].copy()
        
        # Tính tổng tiền đã cúng cho mỗi máy
        summary_bad = df_blacklist.groupby('Mã số máy').agg({
            'Khu vực': 'first',
            'Tình trạng': lambda x: ' | '.join(x.unique()),
            'Tổng chi phí': 'sum',
            'M
