import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Thiết bị Pro", layout="wide")

# Link dữ liệu chuẩn của sếp
PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_final():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # Hàm quét vùng miền thông minh
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
        
        # Dọn dẹp dữ liệu rác
        df = df[df['MÃ_MÁY'] != 'nan']
        df = df[~df['MÃ_MÁY'].str.contains("STT|MÃ|THEO", na=False)]
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

df = load_data_final()

# --- GIAO DIỆN ---
st.title("🛡️ Hệ Thống Quản Trị & Truy Vết Thiết Bị")

# --- PHẦN 1: TRUY VẾT MÃ MÁY (CHỈ NHẬN MÃ SỐ) ---
st.markdown("### 🔍 Tra cứu Hồ sơ thiết bị")
search_query = st.text_input("Nhập chính xác Mã máy (Ví dụ: 2498, 3012...)", key="search_box").strip()

if search_query:
    machine_history = df[df['MÃ_MÁY'] == search_query]
    
    if not machine_history.empty:
        st.info(f"📋 **HỒ SƠ THIẾT BỊ: {search_query}**")
        
        # Chỉ số tình trạng máy
        m1, m2, m3 = st.columns(3)
        num_fixes = len(machine_history)
        vung = machine_history['VÙNG_MIỀN'].iloc[0]
        
        m1.metric("Tổng số lần hỏng", f"{num_fixes} lần")
        m2.metric("Vùng miền", vung)
        
        if num_fixes >= 3:
            m3.error("⚠️ TÌNH TRẠNG: HỎNG QUÁ NHIỀU")
        elif num_fixes == 2:
            m3.warning("⚡ TÌNH TRẠNG: CẦN THEO DÕI")
        else:
            m3.success("✅ TÌNH TRẠNG: BÌNH THƯỜNG")
        
        st.write("**Lịch sử sửa chữa chi tiết:**")
        # Sắp xếp ngày mới nhất lên trên
        history_display = machine_history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN']].sort_values(by='NGAY_FIX', ascending=False)
        st.table(history_display)
        st.divider()
    else:
        st.error(f"❌ Không tìm thấy mã máy '{search_query}' trong hệ thống.")

# --- PHẦN 2: THỐNG KÊ TỔNG QUAN ---
st.markdown("### 📊 Thống kê toàn hệ thống")
c1, c2, c3 = st.columns(3)
c1.metric("Tổng lượt tiếp nhận", f"{len(df):,}")
c2.metric("Số lượng máy hỏng", f"{df['MÃ_MÁY'].nunique():,}")
c3.metric("Số ca Miền Nam", f"{len(df[df['VÙNG_MIỀN'] == 'Miền Nam']):,}")

st.divider()

col_left, col_right = st.columns([6, 4])

with col_left:
    st.subheader("🛠️ Top 10 Lý do hỏng phổ biến (Cột D)")
    reason_counts = df['LÝ_DO_HỎNG'].value_counts().head(10).reset_index()
    reason_counts.columns = ['Lý do', 'Số lượng']
    # Vẽ biểu đồ thanh ngang
    fig_reason = px.bar(reason_counts, x='Số lượng', y='Lý do', orientation='h', 
                       text_auto=True, color='Số lượng', color_continuous_scale='Blues')
    fig_reason.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_reason, use_container_width=True)

with col_right:
    st.subheader("📍 Phân bổ theo Vùng")
    vung_data = df['VÙNG_MIỀN'].value_counts().reset_index()
    # Fix triệt để màu sắc không để bị ngắt quãng
    fig_pie = px.pie(vung_data, values='count', names='VÙNG_MIỀN', hole=0.5,
                    color_discrete_map={
                        "Miền Nam": "#28a745", 
                        "Miền Bắc": "#007bff", 
                        "Miền Trung": "#ffc107",
                        "Khác/Chưa nhập": "#6c757d"
                    })
    st.plotly_chart(fig_pie, use_container_width=True)

with st.expander("📋 Xem 50 nhật ký mới nhất"):
    st.dataframe(df[['MÃ_MÁY', 'VÙNG_MIỀN', 'LÝ_DO_HỎNG', 'COL_6']].tail(50), use_container_width=True)
