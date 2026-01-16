import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Laptop Toàn Quốc", layout="wide")

# Link CSV xuất bản ổn định nhất của sếp
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_final_optimized():
    try:
        # Đọc dữ liệu, bỏ qua các dòng lỗi định dạng
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]

        # TỌA ĐỘ CHUẨN XÁC:
        # COL_1: Mã máy (Cột B)
        # COL_3: Chi nhánh/Vùng miền (Cột D)
        # COL_6: Ngày tháng (Cột G)
        
        def detect_region(row):
            # Quét ưu tiên tại cột COL_3, nếu không có mới quét toàn dòng
            val_col3 = str(row['COL_3']).upper()
            full_text = " ".join(row.astype(str)).upper()
            
            target = val_col3 if "MIỀN" in val_col3 else full_text
            
            if any(x in target for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in target for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in target for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        
        # Xử lý Mã máy: Lấy phần số trước dấu chấm
        df['MÃ_MÁY_SAU_LOC'] = df['COL_1'].astype(str).str.split('.').str[0]
        
        # Xử lý Ngày tháng cho biểu đồ xu hướng
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        
        # Loại bỏ các dòng tiêu đề "THEO DÕI..." hoặc dòng trống
        df = df[df['MÃ_MÁY_SAU_LOC'] != 'nan']
        df = df[~df['MÃ_MÁY_SAU_LOC'].str.contains("STT|MÃ|THEO", na=False)]
        
        return df
    except Exception as e:
        st.error(f"Đang kết nối dữ liệu... ({e})")
        return pd.DataFrame()

df = load_data_final_optimized()

# --- GIAO DIỆN ---
st.markdown("## 🛡️ Hệ thống Quản trị Thiết bị Laptop Pro")

if not df.empty:
    # Sidebar lọc dữ liệu
    with st.sidebar:
        st.header("📍 Bộ lọc")
        list_vung = ["Miền Bắc", "Miền Trung", "Miền Nam", "Khác/Chưa nhập"]
        selected = st.multiselect("Chọn vùng hiển thị", list_vung, default=list_vung)
        st.divider()
        st.download_button("📥 Tải báo cáo CSV", df.to_csv(index=False).encode('utf-8-sig'), "bao_cao.csv")

    df_filtered = df[df['VÙNG_MIỀN'].isin(selected)]

    # KPIs hàng đầu
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng lượt lỗi", f"{len(df_filtered):,}")
    k2.metric("Số máy hỏng", f"{df_filtered['MÃ_MÁY_SAU_LOC'].nunique():,}")
    
    # Tính máy lỗi lặp lại (Hỏng trên 2 lần)
    repeat_df = df_filtered['MÃ_MÁY_SAU_LOC'].value_counts()
    repeat_count = len(repeat_df[repeat_df > 1])
    k3.metric("Máy lỗi lặp lại", repeat_count)
    
    # Hiển thị số dòng thực tế cuối cùng
    k4.metric("Dòng cuối cùng", df.index[-1] if not df.empty else 0)

    st.divider()

    # Biểu đồ
    c_left, c_right = st.columns(2)

    with c_left:
        st.subheader("📊 Phân bổ lỗi theo Vùng")
        vung_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
        vung_data.columns = ['Vùng', 'Số lượng']
        fig1 = px.bar(vung_data, x='Vùng', y='Số lượng', color='Vùng', text_auto=True,
                     color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
        st.plotly_chart(fig1, use_container_width=True)

    with c_right:
        st.subheader("📈 Xu hướng lỗi theo thời gian")
        # Lọc bỏ ngày lỗi (NaT) và sắp xếp
        trend = df_filtered.dropna(subset=['NGAY_FIX'])
        trend = trend.groupby(trend['NGAY_FIX'].dt.date).size().reset_index()
        trend.columns = ['Ngày', 'Số lượng']
        trend = trend.sort_values('Ngày')
        fig2 = px.line(trend, x='Ngày', y='Số lượng', markers=True)
        fig2.update_layout(xaxis_range=[pd.Timestamp('2025-11-01'), pd.Timestamp('2026-02-01')]) # Zoom vào giai đoạn hiện tại
        st.plotly_chart(fig2, use_container_width=True)

    # Danh sách chi tiết
    st.subheader("📋 Danh sách 50 ca mới nhất")
    st.dataframe(df_filtered[['MÃ_MÁY_SAU_LOC', 'VÙNG_MIỀN', 'COL_4', 'COL_6']].tail(50), use_container_width=True)

else:
    st.info("Sếp đợi vài giây để hệ thống bốc dữ liệu từ Google Sheets...")
