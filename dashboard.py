import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG CHUẨN ELITE ---
st.set_page_config(page_title="4ORANGES LAPTOP ELITE", layout="wide", page_icon="🎨")

# CSS để tùy biến Menu và Card chuyên nghiệp hơn
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #f0f2f6;
        transition: all 0.3s;
        border: none;
    }
    .stButton > button:hover {
        background-color: #FF8C00;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #FF8C00;
    }
    </style>
    """, unsafe_allow_html=True)

LOGO_URL = "https://www.4oranges.com/vnt_upload/weblink/Logo_4_Oranges.png"
URL_LAPTOP_LOI = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=675485241&single=true&output=csv"
URL_MIEN_BAC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=602348620&single=true&output=csv"
URL_DA_NANG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=1519063387&single=true&output=csv"

@st.cache_data(ttl=300)
def load_data(url):
    try: return pd.read_csv(url, on_bad_lines='skip', low_memory=False).fillna("")
    except: return pd.DataFrame()

def main():
    # --- SIDEBAR ---
    with st.sidebar:
        st.image(LOGO_URL, use_container_width=True)
        st.markdown("---")
        if st.button('🔄 LÀM MỚI HỆ THỐNG', type="primary"):
            st.cache_data.clear()
            st.rerun()
        
        raw_loi = load_data(URL_LAPTOP_LOI)
        raw_bac = load_data(URL_MIEN_BAC)
        raw_trung = load_data(URL_DA_NANG)

        # Xử lý nhanh dữ liệu tài chính
        f_list = []
        for _, r in raw_loi.iloc[1:].iterrows():
            try:
                ma = str(r.iloc[1]).strip()
                ngay = pd.to_datetime(r.iloc[6], dayfirst=True, errors='coerce')
                if pd.notnull(ngay) and ma:
                    cp = pd.to_numeric(str(r.iloc[8]).replace(',', ''), errors='coerce') or 0
                    f_list.append({"NGÀY": ngay, "NĂM": ngay.year, "THÁNG": ngay.month, "MÃ": ma, "LOẠI": str(r.iloc[3]).strip(), "VÙNG": str(r.iloc[5]).strip(), "CP": cp, "KH": str(r.iloc[2]).strip()})
            except: continue
        df_f = pd.DataFrame(f_list)

        years = sorted(df_f['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", years)
        months = ["Tất cả"] + sorted(df_f[df_f['NĂM'] == sel_year]['THÁNG'].unique().tolist())
        sel_month = st.selectbox("📆 Chọn Tháng", months)

    # --- MAIN INTERFACE ---
    st.title("HỆ THỐNG QUẢN LÝ LAPTOP 4ORANGES")
    
    # 1. KPIs HIGHLIGHT
    df_y = df_f[df_f['NĂM'] == sel_year]
    if sel_month != "Tất cả": df_y = df_y[df_y['THÁNG'] == sel_month]
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("TỔNG CHI PHÍ", f"{df_y['CP'].sum():,.0f} đ")
    with k2: st.metric("SỐ CA XỬ LÝ", f"{len(df_y)} ca")
    with k3: st.metric("TB / CA", f"{(df_y['CP'].mean() if len(df_y)>0 else 0):,.0f} đ")
    with k4: st.metric("VÙNG TRỌNG ĐIỂM", df_y.groupby('VÙNG')['CP'].sum().idxmax() if not df_y.empty else "N/A")

    st.markdown("---")

    # 2. THIẾT KẾ MENU MỚI (PHONG CÁCH CHUYÊN NGHIỆP)
    # Sử dụng st.radio nhưng ẩn giao diện gốc để tạo thanh điều hướng ngang
    menu_options = ["📊 XU HƯỚNG", "💰 TÀI CHÍNH DEEP", "🩺 SỨC KHỎE MÁY", "📦 KHO LOGISTICS", "🧠 AI ĐỀ XUẤT"]
    sel_menu = st.segmented_control("", menu_options, selection_mode="single", default="📊 XU HƯỚNG")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. RENDER NỘI DUNG THEO MENU (GIỮ NGUYÊN LOGIC V22.0)
    if sel_menu == "📊 XU HƯỚNG":
        col1, col2 = st.columns(2)
        with col1: st.plotly_chart(px.pie(df_y, names='VÙNG', title="CƠ CẤU VÙNG MIỀN", hole=0.4, color_discrete_sequence=["#FF8C00", "#FFA500", "#FF4500"]), use_container_width=True)
        with col2:
            df_t = df_y.groupby('THÁNG').size().reset_index(name='Ca')
            st.plotly_chart(px.line(df_t, x='THÁNG', y='Ca', title="BIẾN ĐỘNG THEO THÁNG", markers=True, color_discrete_sequence=["#FF8C00"]), use_container_width=True)

    elif sel_menu == "💰 TÀI CHÍNH DEEP":
        st.plotly_chart(px.treemap(df_y, path=['VÙNG', 'LOẠI'], values='CP', title="CHI TIẾT NGÂN SÁCH", color_discrete_sequence=["#FF8C00", "#D35400"]), use_container_width=True)

    elif sel_menu == "🩺 SỨC KHỎE MÁY":
        health = df_f.groupby('MÃ').agg({'NGÀY': 'count', 'CP': 'sum', 'KH': 'first', 'LOẠI': lambda x: ', '.join(set(x))}).reset_index()
        health.columns = ['Mã Máy', 'Lần hỏng', 'Tổng phí', 'Khách hàng', 'Linh kiện']
        danger = health[health['Lần hỏng'] > 2].sort_values('Lần hỏng', ascending=False)
        st.dataframe(danger.style.format({"Tổng phí": "{:,.0f} đ"}), use_container_width=True)

    elif sel_menu == "📦 KHO LOGISTICS":
        wh_data = []
        for reg, raw in [("MIỀN BẮC", raw_bac), ("MIỀN TRUNG", raw_trung)]:
            for _, r in raw.iloc[1:].iterrows():
                m_id = str(r.iloc[1]).strip()
                if not m_id or "MÃ" in m_id.upper(): continue
                st_nb, st_giao = (str(r.iloc[6]) + str(r.iloc[8])).upper(), str(r.iloc[13]).upper()
                tt = "🟢 ĐÃ TRẢ" if "R" in st_giao else ("🔵 TỒN KHO" if "OK" in st_nb else "🟡 ĐANG SỬA")
                wh_data.append({"VÙNG": reg, "TRẠNG_THÁI": tt})
        df_wh = pd.DataFrame(wh_data)
        st.plotly_chart(px.histogram(df_wh, x="VÙNG", color="TRẠNG_THÁI", barmode="group", color_discrete_map={"🟢 ĐÃ TRẢ": "#FF8C00", "🔵 TỒN KHO": "#F39C12", "🟡 ĐANG SỬA": "#D35400"}), use_container_width=True)

    elif sel_menu == "🧠 AI ĐỀ XUẤT":
        # Giữ nguyên logic tính toán của sếp
        health = df_f.groupby('MÃ').agg({'CP': 'sum'}).reset_index()
        top_bad = health.nlargest(5, 'CP')
        st.error("🚨 DANH SÁCH THIẾT BỊ CẦN THANH LÝ NGAY (CHI PHÍ CAO NHẤT):")
        st.table(top_bad)

if __name__ == "__main__":
    main()
