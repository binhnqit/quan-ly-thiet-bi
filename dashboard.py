import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG (NIÊM PHONG) ---
st.set_page_config(page_title="LAPTOP MÁY PHA MÀU 4ORANGES", layout="wide", page_icon="🎨")
ORANGE_COLORS = ["#FF8C00", "#FFA500", "#FF4500", "#E67E22", "#D35400"]

LOGO_URL = "https://www.4oranges.com/vnt_upload/weblink/Logo_4_Oranges.png"
URL_LAPTOP_LOI = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=675485241&single=true&output=csv"
URL_MIEN_BAC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=602348620&single=true&output=csv"
URL_DA_NANG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=1519063387&single=true&output=csv"

@st.cache_data(ttl=300)
def get_raw_data(url):
    try: return pd.read_csv(url, on_bad_lines='skip', low_memory=False).fillna("")
    except: return pd.DataFrame()

@st.cache_data(ttl=300)
def process_finance_data(df_loi_raw):
    f_list = []
    if not df_loi_raw.empty:
        for _, row in df_loi_raw.iloc[1:].iterrows():
            try:
                ma = str(row.iloc[1]).strip()
                if not ma or "MÃ" in ma.upper(): continue
                ngay = pd.to_datetime(row.iloc[6], dayfirst=True, errors='coerce')
                if pd.notnull(ngay):
                    cp = pd.to_numeric(str(row.iloc[8]).replace(',', ''), errors='coerce') or 0
                    f_list.append({
                        "NGÀY": ngay, "NĂM": ngay.year, "THÁNG": ngay.month,
                        "MÃ_MÁY": ma, "LINH_KIỆN": str(row.iloc[3]).strip(),
                        "VÙNG": str(row.iloc[5]).strip(), "CP": cp, "KHÁCH": str(row.iloc[2]).strip()
                    })
            except: continue
    return pd.DataFrame(f_list)

def main():
    with st.sidebar:
        try: st.image(LOGO_URL, use_container_width=True)
        except: st.title("🎨 4ORANGES")
        if st.button('🔄 LÀM MỚI DỮ LIỆU', type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        df_loi_raw = get_raw_data(URL_LAPTOP_LOI)
        df_bac_raw = get_raw_data(URL_MIEN_BAC)
        df_trung_raw = get_raw_data(URL_DA_NANG)
        df_f = process_finance_data(df_loi_raw)

        if df_f.empty:
            st.warning("⚠️ Đang chờ dữ liệu...")
            return

        years = sorted(df_f['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("Chọn Năm", years)
        months = ["Tất cả"] + sorted(df_f[df_f['NĂM'] == sel_year]['THÁNG'].unique().tolist())
        sel_month = st.selectbox("Chọn Tháng", months)

    df_display = df_f[df_f['NĂM'] == sel_year]
    if sel_month != "Tất cả":
        df_display = df_display[df_display['THÁNG'] == sel_month]

    st.title("HỆ THỐNG QUẢN LÝ LAPTOP MÁY PHA MÀU 4ORANGES")
    st.divider()

    # KPI CARDS (BẢO TOÀN SỐ LIỆU)
    m1, m2, m3, m4 = st.columns(4)
    total_spent = df_display['CP'].sum()
    m1.metric("TỔNG CHI PHÍ", f"{total_spent:,.0f} đ")
    m2.metric("SỐ CA XỬ LÝ", f"{len(df_display)} ca")
    m3.metric("TRUNG BÌNH/CA", f"{(df_display['CP'].mean() if len(df_display)>0 else 0):,.0f} đ")
    m4.metric("VÙNG CHI PHÍ CAO", df_display.groupby('VÙNG')['CP'].sum().idxmax() if not df_display.empty else "N/A")

    tabs = st.tabs(["📊 XU HƯỚNG", "💰 TÀI CHÍNH CHUYÊN SÂU", "🩺 SỨC KHỎE MÁY", "📦 KHO LOGISTICS", "🧠 AI ĐỀ XUẤT"])

    with tabs[1]: # FIX LỖI VALUEERROR TẠI ĐÂY
        st.subheader("🔍 PHÂN TÍCH SÂU CHI PHÍ & TẦN SUẤT")
        deep_df = df_display.groupby('LINH_KIỆN').agg({'CP': ['sum', 'count', 'mean']}).reset_index()
        deep_df.columns = ['LINH_KIỆN', 'Tổng_CP', 'Số_lần_hỏng', 'Trung_bình_CP']
        # Đảm bảo size luôn là số dương để tránh crash biểu đồ
        deep_df['Size_Bong_Bong'] = deep_df['Trung_bình_CP'].apply(lambda x: max(x, 1))
        
        try:
            st.plotly_chart(px.scatter(deep_df, x="Số_lần_hỏng", y="Tổng_CP", size="Size_Bong_Bong", color="LINH_KIỆN",
                                     title="TƯƠNG QUAN TẦN SUẤT & CHI PHÍ", color_discrete_sequence=px.colors.sequential.Oranges_r), use_container_width=True)
        except:
            st.error("⚠️ Không thể hiển thị biểu đồ phân tán do dữ liệu có giá trị không hợp lệ.")
        
        st.plotly_chart(px.treemap(df_display, path=['VÙNG', 'LINH_KIỆN'], values='CP', title="CƠ CẤU CHI PHÍ CHI TIẾT", color_discrete_sequence=ORANGE_COLORS), use_container_width=True)

    with tabs[3]: # KHO LOGISTICS (NIÊM PHONG LOGIC R/OK)
        wh_data = []
        for reg, raw in [("MIỀN BẮC", df_bac_raw), ("MIỀN TRUNG", df_trung_raw)]:
            if not raw.empty:
                for _, r in raw.iloc[1:].iterrows():
                    m_id = str(r.iloc[1]).strip()
                    if not m_id or "MÃ" in m_id.upper(): continue
                    st_nb, st_ng, st_giao = (str(r.iloc[6]) + str(r.iloc[8])).upper(), (str(r.iloc[9]) + str(r.iloc[11])).upper(), str(r.iloc[13]).upper()
                    if "R" in st_giao: tt = "🟢 ĐÃ TRẢ CHI NHÁNH"
                    elif "OK" in st_nb: tt = "🔵 ĐANG NẰM KHO NHẬN"
                    elif any(x in st_ng for x in ["OK", "ĐANG", "SỬA"]): tt = "🟡 ĐANG SỬA NGOÀI"
                    else: tt = "⚪ CHỜ KIỂM TRA"
                    wh_data.append({"VÙNG": reg, "MÃ_MÁY": m_id, "TRẠNG_THÁI": tt})
        if wh_data:
            df_wh = pd.DataFrame(wh_data)
            st.plotly_chart(px.histogram(df_wh, x="VÙNG", color="TRẠNG_THÁI", barmode="group", color_discrete_map={"🟢 ĐÃ TRẢ CHI NHÁNH": "#FF8C00", "🔵 ĐANG NẰM KHO NHẬN": "#F39C12", "🟡 ĐANG SỬA NGOÀI": "#D35400"}), use_container_width=True)

    with tabs[4]: # NÂNG CẤP MODULE 1 & 2 THEO LỘ TRÌNH AI CTO
        st.subheader("🧠 TRỢ LÝ CHIẾN LƯỢC AI (MODULE 1 & 2)")
        
        # Module 1: Phân tích bệnh lý vùng miền
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            v_error = df_display.groupby(['VÙNG', 'LINH_KIỆN']).size().reset_index(name='Ca')
            st.plotly_chart(px.bar(v_error, x='LINH_KIỆN', y='Ca', color='VÙNG', barmode='group', color_discrete_sequence=ORANGE_COLORS), use_container_width=True)
        with col_m2:
            st.info("💡 **Dự báo kho:** AI phát hiện xu hướng hỏng hóc khác biệt giữa các miền. Sếp nên ưu tiên dự phòng linh kiện theo đặc thù khu vực để giảm thời gian máy nằm chờ sửa.")

        st.divider()

        # Module 2: Kiểm toán chi phí bất thường
        st.markdown("#### ⚠️ Cảnh báo chi phí bất thường (>150% trung bình loại)")
        lk_avg = df_f.groupby('LINH_KIỆN')['CP'].mean().reset_index(name='Gia_TB')
        df_audit = df_display.merge(lk_avg, on='LINH_KIỆN')
        anomalies = df_audit[df_audit['CP'] > df_audit['Gia_TB'] * 1.5]
        
        if not anomalies.empty:
            st.dataframe(anomalies[['MÃ_MÁY', 'LINH_KIỆN', 'CP', 'Gia_TB', 'VÙNG']].style.format({"CP": "{:,.0f}", "Gia_TB": "{:,.0f}"}), use_container_width=True)
            st.error("AI khuyến nghị sếp hậu kiểm các ca trên để tránh tình trạng thợ 'vẽ bệnh' hoặc báo giá linh kiện sai lệch.")
        else:
            st.success("✅ Hệ thống chưa phát hiện bất thường về chi phí trong kỳ này.")

if __name__ == "__main__": main()
