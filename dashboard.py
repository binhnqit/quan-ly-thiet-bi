import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Laptop Management System PRO", layout="wide")

# Link dữ liệu chuẩn của sếp
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_enterprise():
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
        
        df = df[df['MÃ_MÁY'] != 'nan']
        df = df[~df['MÃ_MÁY'].str.contains("STT|MÃ|THEO", na=False)]
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

df = load_data_enterprise()

# --- SIDEBAR: BỘ LỌC HỆ THỐNG ---
with st.sidebar:
    st.header("⚙️ Bộ lọc hệ thống")
    list_vung = ["Miền Bắc", "Miền Trung", "Miền Nam"]
    selected_vung = st.multiselect("Lọc theo Vùng", list_vung, default=list_vung)
    
    # Lọc theo tháng
    df['MONTH'] = df['NGAY_FIX'].dt.month
    list_month = sorted([int(m) for m in df['MONTH'].unique() if pd.notna(m)])
    selected_month = st.multiselect("Lọc theo Tháng", options=list_month, default=list_month, format_func=lambda x: f"Tháng {x}")
    
    st.divider()
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Tải báo cáo CSV", data=csv_data, file_name="bao_cao_laptop.csv", mime="text/csv")

# Áp dụng bộ lọc cho Dashboard chung
df_filtered = df[(df['VÙNG_MIỀN'].isin(selected_vung)) & (df['MONTH'].isin(selected_month))]

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Hệ Thống Quản Trị Thiết Bị Tập Đoàn")

# --- PHẦN 1: TRUY VẾT MÃ MÁY (ĐỘC LẬP) ---
st.markdown("### 🔍 Truy tìm Hồ sơ bệnh án")
search_query = st.text_input("Nhập Mã máy để truy vết lịch sử (VD: 2498, 3012...)", key="search_box").strip()

if search_query:
    machine_history = df[df['MÃ_MÁY'] == search_query]
    if not machine_history.empty:
        with st.container():
            st.info(f"📋 **HỒ SƠ THIẾT BỊ: {search_query}**")
            m1, m2, m3 = st.columns(3)
            num_fixes = len(machine_history)
            m1.metric("Tổng lần hỏng", f"{num_fixes} lần")
            m2.metric("Khu vực", machine_history['VÙNG_MIỀN'].iloc[0])
            
            if num_fixes >= 3:
                status, color = "🚨 NGUY CƠ CAO", "inverse"
            elif num_fixes == 2:
                status, color = "⚠️ CẦN THEO DÕI", "off"
            else:
                status, color = "✅ BÌNH THƯỜNG", "normal"
            
            m3.metric("Tình trạng", status)
            
            history_display = machine_history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']].sort_values(by='NGAY_FIX', ascending=False)
            st.table(history_display)
    else:
        st.error(f"❌ Không tìm thấy mã máy '{search_query}'")

st.divider()

# --- PHẦN 2: THỐNG KÊ TỔNG QUAN ---
st.markdown("### 📊 Dashboard Phân tích chung")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tổng lượt lỗi", f"{len(df_filtered):,}")
c2.metric("Số máy đang lỗi", f"{df_filtered['MÃ_MÁY'].nunique():,}")

repeat_df = df_filtered['MÃ_MÁY'].value_counts()
critical_count = len(repeat_df[repeat_df >= 3])
c3.metric("🚨 Máy hỏng nặng (>=3 lần)", critical_count)

top_reason = df_filtered['LÝ_DO_HỎNG'].mode()[0] if not df_filtered.empty else "N/A"
c4.metric("Lý do phổ biến", top_reason)

st.divider()

# BIỂU ĐỒ 
col_left, col_right = st.columns([6, 4])

with col_left:
    st.subheader("🛠️ Top 15 Lý do hỏng / Linh kiện (Cột D)")
    reason_counts = df_filtered['LÝ_DO_HỎNG'].value_counts().head(15).reset_index()
    reason_counts.columns = ['Lý do', 'Số lượng']
    fig_reason = px.bar(reason_counts, x='Số lượng', y='Lý do', orientation='h', 
                       text_auto=True, color='Số lượng', color_continuous_scale='Reds')
    fig_reason.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_reason, use_container_width=True)

with col_right:
    st.subheader("📍 Tỷ lệ lỗi theo Vùng")
    vung_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
    fig_pie = px.pie(vung_data, values='count', names='VÙNG_MIỀN', hole=0.5,
                    color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
    st.plotly_chart(fig_pie, use_container_width=True)

# THỐNG KÊ DANH SÁCH ĐEN
st.subheader("🚩 Top 10 Máy hỏng nhiều lần nhất")
bad_machines = repeat_df.head(10).reset_index()
bad_machines.columns = ['Mã Máy', 'Số lần hỏng']
st.dataframe(bad_machines, use_container_width=True)

with st.expander("📋 Xem toàn bộ nhật ký chi tiết"):
    st.dataframe(df_filtered[['MÃ_MÁY', 'VÙNG_MIỀN', 'LÝ_DO_HỎNG', 'COL_6']].tail(100), use_container_width=True)
