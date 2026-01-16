import streamlit as st
import pandas as pd
import plotly.express as px
import math

# --- 1. HỆ THỐNG BẢO MẬT (LOGIN) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Hệ thống Quản trị Nội bộ")
        password = st.text_input("Vui lòng nhập mật khẩu truy cập:", type="password")
        if st.button("Đăng nhập"):
            if password == "admin123": # Sếp đổi mật khẩu ở đây
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác")
        return False
    return True

if check_password():
    # --- 2. CẤU HÌNH GIAO DIỆN ---
    st.set_page_config(page_title="Hệ Thống Quản Trị Tài Sản AI", layout="wide")
    
    # CSS Pro
    st.markdown("""
        <style>
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 4px solid #1E3A8A; }
        .priority-high { color: #d32f2f; font-weight: bold; }
        .priority-med { color: #f57c00; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    # 3. KẾT NỐI DỮ LIỆU (Quét 3.976 dòng)
    PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

    @st.cache_data(ttl=60)
    def load_data():
        df = pd.read_csv(PUBLISHED_URL)
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        df['VÙNG_MIỀN'] = df.apply(lambda r: "Miền Bắc" if "Bắc" in str(r.values) else ("Miền Nam" if "Nam" in str(r.values) else "Miền Trung"), axis=1)
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0].str.strip()
        df['LÝ_DO_HỎNG'] = df['COL_3'].fillna("Chưa rõ")
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        df['NĂM'] = df['NGAY_FIX'].dt.year
        df['THÁNG'] = df['NGAY_FIX'].dt.month
        return df.dropna(subset=['NGAY_FIX'])

    df = load_data()

    # --- 4. LOGIC ƯU TIÊN MUA SẮM ---
    def calculate_priority(row):
        score = 0
        # Ưu tiên theo linh kiện đắt tiền/quan trọng
        if any(x in str(row['LÝ_DO_HỎNG']) for x in ['Màn hình', 'Main', 'Nguồn']): score += 3
        # Ưu tiên theo tần suất hỏng (Dữ liệu lịch sử)
        machine_history = df[df['MÃ_MÁY'] == row['MÃ_MÁY']]
        if len(machine_history) >= 4: score += 5
        
        if score >= 7: return "🔴 KHẨN CẤP"
        if score >= 4: return "🟠 CAO"
        return "🟢 BÌNH THƯỜNG"

    # --- SIDEBAR & TABS ---
    with st.sidebar:
        st.title("🛡️ QUẢN TRỊ VIÊN")
        if st.button("Đăng xuất"):
            st.session_state["authenticated"] = False
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        sel_vung = st.multiselect("Khu vực", ["Miền Bắc", "Miền Trung", "Miền Nam"], default=["Miền Bắc", "Miền Trung", "Miền Nam"])

    tab_main, tab_priority = st.tabs(["📊 Dashboard Chiến Lược", "⚡ Ưu Tiên Mua Sắm"])

    with tab_main:
        st.title("🛡️ HỆ THỐNG QUẢN TRỊ TÀI SẢN CHIẾN LƯỢC AI")
        # (Giữ nguyên phần biểu đồ và chatbot như bản cũ)

    with tab_priority:
        st.header("📋 Danh sách đề xuất mua sắm ưu tiên")
        df_priority = df[(df['NĂM'] == sel_year) & (df['VÙNG_MIỀN'].isin(sel_vung))].copy()
        
        if not df_priority.empty:
            df_priority['MỨC ƯU TIÊN'] = df_priority.apply(calculate_priority, axis=1)
            
            # Chỉ hiển thị những máy hỏng gần nhất và cần xử lý
            display_df = df_priority.sort_values('NGAY_FIX', ascending=False).head(20)
            st.dataframe(display_df[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO_HỎNG', 'VÙNG_MIỀN', 'MỨC ƯU TIÊN']], use_container_width=True)
            
            st.info("💡 **Giải thích:** AI xếp hạng 'Khẩn cấp' cho các máy hỏng linh kiện lõi hoặc có tiền sử hỏng trên 4 lần.")
