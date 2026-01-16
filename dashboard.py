import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Laptop Management PRO", layout="wide")

PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_v5():
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
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

df = load_data_v5()

# --- GIAO DIỆN ---
st.title("🛡️ Hệ Thống Truy Vết & Quản Trị Thiết Bị")

# --- PHẦN 1: Ô TÌM KIẾM CHIẾN LƯỢC ---
st.markdown("### 🔍 Truy tìm lịch sử máy")
search_query = st.text_input("Gõ Mã máy để xem bệnh án (VD: 2498, 3012...)", key="search_box")

if search_query:
    # Lọc riêng con máy được tìm kiếm
    machine_history = df[df['MÃ_MÁY'] == search_query.strip()]
    
    if not machine_history.empty:
        st.success(f"✅ Đã tìm thấy dữ liệu cho máy: **{search_query}**")
        
        # Hiển thị thẻ tình trạng máy
        m1, m2, m3 = st.columns(3)
        num_fixes = len(machine_history)
        vung = machine_history['VÙNG_MIỀN'].iloc[0]
        
        m1.metric("Tổng số lần hỏng", f"{num_fixes} lần")
        m2.metric("Khu vực quản lý", vung)
        
        # Cảnh báo nếu hỏng quá nhiều
        status = "Bình thường" if num_fixes < 3 else "⚠️ CẢNH BÁO: HỎNG QUÁ NHIỀU"
        m3.metric("Tình trạng thiết bị", status)
        
        # Bảng lịch sử hỏng của riêng máy đó
        st.write(f"**Lịch sử sửa chữa chi tiết của máy {search_query}:**")
        st.table(machine_history[['NGAY_FIX', 'LÝ_DO_HỎNG', 'COL_4']].sort_values(by='NGAY_FIX', ascending=False))
        st.divider()
    else:
        st.warning(f"❌ Không tìm thấy mã máy '{search_query}' trong hệ thống. Sếp kiểm tra lại mã nhé!")

# --- PHẦN 2: THỐNG KÊ TỔNG QUAN ---
st.markdown("### 📊 Tổng quan hệ thống")
c1, c2, c3 = st.columns(3)
c1.metric("Tổng lượt lỗi", f"{len(df):,}")
c2.metric("Số máy khác nhau", f"{df['MÃ_MÁY'].nunique():,}")
c3.metric("Miền Nam", f"{len(df[df['VÙNG_MIỀN'] == 'Miền Nam']):,}")

st.divider()

# BIỂU ĐỒ LÝ DO HỎNG (Cột D)
st.subheader("🛠️ Những lý do hỏng phổ biến nhất")
reason_counts = df['LÝ_DO_HỎNG'].value_counts().head(10).reset_index()
reason_counts.columns = ['Lý do', 'Số lượng']
fig_reason = px.bar(reason_counts, x='Số lượng', y='Lý do', orientation='h', 
                   text_auto=True, color='Số lượng', color_continuous_scale='Reds')
st.plotly_chart(fig_reason, use_container_width=True)

# BẢNG DỮ LIỆU TỔNG
with st.expander("📋 Xem toàn bộ nhật ký (Dòng mới nhất)"):
    st.dataframe(df[['MÃ_MÁY', 'VÙNG_MIỀN', 'LÝ_DO_HỎNG', 'COL_6']].tail(50), use_container_width=True)
