import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Laptop Pro", layout="wide")

PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_v3():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # 1. Xác định Vùng Miền (Quét toàn dòng để không sót)
        def detect_region(row):
            text = " ".join(row.astype(str)).upper()
            if any(x in text for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in text for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in v for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        
        # 2. XÁC ĐỊNH LÝ DO HỎNG (CHÍNH LÀ CỘT D - COL_3)
        # Sếp muốn tập trung vào cột này để thống kê linh kiện
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa ghi chú").astype(str).str.strip()
        
        # 3. Mã máy (Cột B - COL_1)
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0]
        
        # 4. Ngày tháng (Cột G - COL_6)
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        
        # Lọc rác
        df = df[df['MÃ_MÁY'] != 'nan']
        df = df[~df['MÃ_MÁY'].str.contains("STT|MÃ|THEO", na=False)]
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

df = load_data_v3()

# --- GIAO DIỆN ---
st.title("🛡️ Dashboard Phân Tích Linh Kiện & Lý Do Hỏng")

if not df.empty:
    # Sidebar
    with st.sidebar:
        st.header("🔍 Lọc & Tìm kiếm")
        search = st.text_input("Tìm Mã máy hoặc Lý do...", placeholder="Ví dụ: Phím, Pin...")
        selected_vung = st.multiselect("Vùng miền", ["Miền Bắc", "Miền Trung", "Miền Nam"], default=["Miền Bắc", "Miền Trung", "Miền Nam"])
        st.divider()
        st.info(f"Tổng dữ liệu: {len(df)} dòng")

    # Filter dữ liệu
    mask = df['VÙNG_MIỀN'].isin(selected_vung)
    if search:
        mask = mask & (df['MÃ_MÁY'].str.contains(search, case=False) | df['LÝ_DO_HỎNG'].str.contains(search, case=False))
    df_filtered = df[mask]

    # KPI Hàng đầu
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng lượt tiếp nhận", f"{len(df_filtered):,}")
    c2.metric("Số máy phát sinh lỗi", f"{df_filtered['MÃ_MÁY'].nunique():,}")
    
    # Tìm lý do hỏng phổ biến nhất
    top_reason = df_filtered['LÝ_DO_HỎNG'].mode()[0] if not df_filtered.empty else "N/A"
    c3.metric("Lý do hỏng nhiều nhất", top_reason)

    st.divider()

    # BIỂU ĐỒ CHÍNH
    col_a, col_b = st.columns([6, 4])

    with col_a:
        st.subheader("🛠️ Thống kê Lý do hỏng / Linh kiện (Cột D)")
        # Lấy top 15 lý do để biểu đồ không bị rối
        reason_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(15).reset_index()
        reason_counts.columns = ['Lý do', 'Số lượng']
        fig_reason = px.bar(reason_counts, x='Số lượng', y='Lý do', orientation='h', 
                           text_auto=True, color='Lý do', color_discrete_sequence=px.colors.qualitative.Prism)
        fig_reason.update_layout(showlegend=False)
        st.plotly_chart(fig_reason, use_container_width=True)

    with col_b:
        st.subheader("📍 Tỷ lệ lỗi theo Vùng")
        vung_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
        fig_pie = px.pie(vung_data, values='count', names='VÙNG_MIỀN', hole=0.5,
                        color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
        st.plotly_chart(fig_pie, use_container_width=True)

    # DANH SÁCH CHI TIẾT THEO DÕI
    st.divider()
    st.subheader("📋 Chi tiết các ca sửa chữa")
    # Hiển thị Mã máy, Vùng, Lý do (Cột D), và Ngày
    st.dataframe(df_filtered[['MÃ_MÁY', 'VÙNG_MIỀN', 'LÝ_DO_HỎNG', 'COL_6']].tail(100), use_container_width=True)

else:
    st.warning("Đang kết nối dữ liệu...")
