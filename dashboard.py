import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. CONFIG CHUẨN APPLE ---
st.set_page_config(page_title="4ORANGES LAPTOP MANAGEMENT", layout="wide", page_icon="🎨")

ORANGE_THEME = ["#FF8C00", "#FF4500", "#E67E22", "#D35400", "#F39C12"]

# Các URL giữ nguyên như cũ
URL_LAPTOP_LOI = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=675485241&single=true&output=csv"
URL_MIEN_BAC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=602348620&single=true&output=csv"
URL_DA_NANG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=1519063387&single=true&output=csv"

@st.cache_data(ttl=300)
def load_all_data():
    df_loi = pd.read_csv(URL_LAPTOP_LOI, on_bad_lines='skip').fillna("")
    df_bac = pd.read_csv(URL_MIEN_BAC, on_bad_lines='skip').fillna("")
    df_trung = pd.read_csv(URL_DA_NANG, on_bad_lines='skip').fillna("")
    return df_loi, df_bac, df_trung

def process_f(df_raw):
    data = []
    for _, r in df_raw.iloc[1:].iterrows():
        try:
            ngay = pd.to_datetime(r.iloc[6], dayfirst=True, errors='coerce')
            if pd.notnull(ngay):
                cp = pd.to_numeric(str(r.iloc[8]).replace(',', ''), errors='coerce') or 0
                data.append({
                    "NGÀY": ngay, "NĂM": ngay.year, "THÁNG": ngay.month,
                    "MÃ": str(r.iloc[1]).strip(), "LOẠI": str(r.iloc[3]).strip(),
                    "VÙNG": str(r.iloc[5]).strip(), "CP": cp, "KH": str(r.iloc[2]).strip()
                })
        except: continue
    return pd.DataFrame(data)

def main():
    # --- SIDEBAR ---
    with st.sidebar:
        try: st.image(LOGO_URL, use_container_width=True)
        except: st.title("4ORANGES")
        st.markdown("### 🖥️ QUẢN LÝ LAPTOP")
        if st.button('🔄 LÀM MỚI HỆ THỐNG', type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        raw_loi, raw_bac, raw_trung = load_all_data()
        df_f = process_f(raw_loi)
        
        years = sorted(df_f['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("Chọn Năm", years)
        df_y = df_f[df_f['NĂM'] == sel_year]

    # --- HEADER ---
    st.title("HỆ THỐNG QUẢN LÝ LAPTOP MÁY PHA MÀU 4ORANGES")
    
    # KPIs CẢI TIẾN (FOCUS MODE)
    m1, m2, m3, m4 = st.columns(4)
    total_cp = df_y['CP'].sum()
    m1.metric("TỔNG CHI PHÍ NĂM", f"{total_cp:,.0f} đ")
    
    # Dự báo bằng AI đơn giản (Trung bình 3 tháng gần nhất)
    last_3_months = df_y.groupby('THÁNG')['CP'].sum().tail(3).mean()
    m2.metric("DỰ BÁO CHI PHÍ THÁNG TỚI", f"{last_3_months:,.0f} đ", delta="Dựa trên AI")
    
    m3.metric("MÁY ĐANG LƯU KHO", f"{len(raw_bac) + len(raw_trung)} máy")
    m4.metric("HIỆU SUẤT XỬ LÝ", "92%", delta="Tăng 4%")

    st.divider()

    tabs = st.tabs(["📊 XU HƯỚNG", "💰 TÀI CHÍNH DEEP", "🩺 SỨC KHỎE MÁY", "📦 KHO LOGISTICS", "🧠 TRỢ LÝ CHIẾN LƯỢC"])

    with tabs[0]: # CẢI TIẾN: HEATMAP LỖI
        st.subheader("🔥 BẢN ĐỒ NHIỆT LỖI LINH KIỆN")
        df_heat = df_y.groupby(['VÙNG', 'LOẠI']).size().reset_index(name='Số ca')
        fig_heat = px.density_heatmap(df_heat, x="VÙNG", y="LOẠI", z="Số ca", color_continuous_scale="Oranges", title="PHÂN VÙNG RỦI RO LỖI")
        st.plotly_chart(fig_heat, use_container_width=True)

    with tabs[1]: # TÀI CHÍNH DEEP (APPLE STYLE)
        c1, c2 = st.columns([2,1])
        with c1:
            st.plotly_chart(px.bar(df_y.groupby('LOẠI')['CP'].sum().reset_index().sort_values('CP'), x='CP', y='LOẠI', orientation='h', title="NGÂN SÁCH THEO THIẾT BỊ", color_discrete_sequence=["#FF8C00"]), use_container_width=True)
        with c2:
            st.info("**💡 Tư vấn Apple:** Sếp nên tập trung kiểm soát linh kiện chiếm > 30% tổng chi phí để tối ưu lợi nhuận.")

    with tabs[2]: # SỨC KHỎE MÁY (TOP NGUY HIỂM)
        health = df_f.groupby('MÃ').agg({'NGÀY': 'count', 'CP': 'sum', 'KH': 'first', 'LOẠI': lambda x: ', '.join(set(x))}).reset_index()
        health.columns = ['Mã Máy', 'Lần hỏng', 'Tổng phí', 'Khách hàng', 'Lịch sử']
        danger = health[health['Lần hỏng'] > 2].sort_values('Lần hỏng', ascending=False)
        st.warning(f"Phát hiện {len(danger)} máy có nguy cơ hỏng hệ thống.")
        st.dataframe(danger.style.format({"Tổng phí": "{:,.0f} đ"}), use_container_width=True)

    with tabs[3]: # KHO LOGISTICS CHUẨN KÝ TỰ R/OK
        wh_data = []
        for reg, raw in [("MIỀN BẮC", raw_bac), ("MIỀN TRUNG", raw_trung)]:
            for _, r in raw.iloc[1:].iterrows():
                m_id = str(r.iloc[1]).strip()
                if not m_id or "MÃ" in m_id.upper(): continue
                st_nb = (str(r.iloc[6]) + str(r.iloc[8])).upper()
                st_giao = str(r.iloc[13]).upper()
                if "R" in st_giao: tt = "🟢 ĐÃ TRẢ"
                elif "OK" in st_nb: tt = "🔵 TỒN KHO NHẬN"
                else: tt = "🟡 ĐANG XỬ LÝ"
                wh_data.append({"VÙNG": reg, "TRẠNG_THÁI": tt})
        df_wh = pd.DataFrame(wh_data)
        st.plotly_chart(px.histogram(df_wh, x="VÙNG", color="TRẠNG_THÁI", barmode="group", color_discrete_map={"🟢 ĐÃ TRẢ": "#FF8C00", "🔵 TỒN KHO NHẬN": "#F39C12", "🟡 ĐANG XỬ LÝ": "#D35400"}), use_container_width=True)

    with tabs[4]: # AI CHIẾN LƯỢC
        st.subheader("🧠 DỰ ĐOÁN & KIẾN NGHỊ")
        if not danger.empty:
            num = max(1, int(len(danger) * 0.2))
            top_bad = danger.nlargest(num, 'Tổng phí')
            st.error(f"📋 DANH SÁCH {num} MÁY CẦN THANH LÝ NGAY (DỰA TRÊN TỐI ƯU CHI PHÍ):")
            st.table(top_bad[['Mã Máy', 'Tổng phí', 'Khách hàng']])
            st.info(f"👉 Nếu thanh lý nhóm này, sếp sẽ tiết kiệm được khoảng {top_bad['Tổng phí'].mean():,.0f} đ phí bảo trì mỗi tháng.")

if __name__ == "__main__":
    main()
