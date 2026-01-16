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
        
        # Mapping cột linh hoạt
        mapping = {
            'MÃ SỐ MÁY': next((c for c in df.columns if "MÁY" in c), None),
            'KHU VỰC': next((c for c in df.columns if "KHU VỰC" in c or "CHI NHÁNH" in c), None),
            'TÌNH TRẠNG': next((c for c in df.columns if "TRẠNG" in c or "KIỂM TRA" in c), None),
            'SỬA NỘI BỘ': next((c for c in df.columns if "NỘI BỘ" in c), None),
            'SỬA BÊN NGOÀI': next((c for c in df.columns if "NGOÀI" in c), None)
        }

        if mapping['MÃ SỐ MÁY']:
            # Làm sạch dữ liệu: Bỏ dòng không có mã máy, lấp đầy ô trống ở Khu vực
            df = df.dropna(subset=[mapping['MÃ SỐ MÁY']])
            df['Mã số máy'] = df[mapping['MÃ SỐ MÁY']].astype(str).str.split('.').str[0].str.strip()
            
            # Xử lý Khu vực: Chuyển về chuỗi và thay thế NaN bằng "Chưa phân loại"
            df['Khu vực'] = df[mapping['KHU VỰC']].astype(str).replace(['nan', 'None', ''], 'Chưa phân loại') if mapping['KHU VỰC'] else "N/A"
            df['Tình trạng'] = df[mapping['TÌNH TRẠNG']].astype(str).replace(['nan', 'None', ''], 'N/A') if mapping['TÌNH TRẠNG'] else "N/A"
            
            # Xử lý chi phí
            for col in [mapping['SỬA NỘI BỘ'], mapping['SỬA BÊN NGOÀI']]:
                if col:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Tính tổng chi phí
            col_noi_bo = mapping['SỬA NỘI BỘ'] if mapping['SỬA NỘI BỘ'] else None
            col_ngoai = mapping['SỬA BÊN NGOÀI'] if mapping['SỬA BÊN NGOÀI'] else None
            
            df['Tổng chi phí'] = 0
            if col_noi_bo: df['Tổng chi phí'] += df[col_noi_bo]
            if col_ngoai: df['Tổng chi phí'] += df[col_ngoai]
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

df_raw = load_data_full()

# --- SIDEBAR: BỘ LỌC ---
st.sidebar.header("🔍 BỘ LỌC DỮ LIỆU")
if not df_raw.empty:
    # SỬA LỖI TẠI ĐÂY: Chuyển hết sang string trước khi sorted để tránh lỗi TypeError
    raw_areas = df_raw['Khu vực'].unique().tolist()
    clean_areas = sorted([str(area) for area in raw_areas if area is not None])
    all_areas = ["Tất cả"] + clean_areas
    
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
    c2.metric("Tổng chi phí", f"{df['Tổng chi phí'].sum():,.0f} VNĐ")
    
    counts = df['Mã số máy'].value_counts()
    bad_devices = counts[counts >= 2]
    c3.metric("Máy hỏng ≥ 2 lần", len(bad_devices))
    c4.metric("Khu vực đang xem", selected_area)

    st.divider()

    # 2. Biểu đồ
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("💰 Chi phí theo Khu vực")
        cost_chart = df.groupby('Khu vực')['Tổng chi phí'].sum().reset_index()
        cost_chart.columns = ['Khu vực', 'Số tiền']
        fig_cost = px.bar(cost_chart, x='Khu vực', y='Số tiền', color='Khu vực', text_auto='.2s')
        st.plotly_chart(fig_cost, use_container_width=True)

    with col_right:
        st.subheader("🧩 Cơ cấu loại hư hỏng")
        reason_chart = df['Tình trạng'].value_counts().reset_index()
        reason_chart.columns = ['Lý do', 'Số lượng']
        fig_pie = px.pie(reason_chart, names='Lý do', values='Số lượng', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # 3. Danh sách máy "Đen" (Cảnh báo thanh lý)
    if not bad_devices.empty:
        st.subheader("🚨 DANH SÁCH MÁY CẦN THEO DÕI ĐẶC BIỆT")
        df_blacklist = df[df['Mã số máy'].isin(bad_devices.index)].copy()
        summary_bad = df_blacklist.groupby('Mã số máy').agg({
            'Khu vực': 'first',
            'Tình trạng': lambda x: ' | '.join(x.unique()),
            'Tổng chi phí': 'sum',
            'Mã số máy': 'count'
        }).rename(columns={'Mã số máy': 'Số lần hỏng'}).reset_index()
        
        st.dataframe(summary_bad.sort_values('Số lần hỏng', ascending=False), use_container_width=True)
    
    # 4. Bảng dữ liệu thô
    with st.expander("🔍 Xem toàn bộ Nhật ký chi tiết"):
        st.dataframe(df, use_container_width=True)
else:
    st.info("Đang chờ dữ liệu từ Google Sheets...")
