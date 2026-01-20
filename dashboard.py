import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG (GIỮ NGUYÊN) ---
st.set_page_config(page_title="LAPTOP MÁY PHA MÀU 4ORANGES", layout="wide", page_icon="🎨")
ORANGE_COLORS = ["#FF8C00", "#FFA500", "#FF4500", "#E67E22", "#D35400"]

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
    # --- SIDEBAR (GIỮ NGUYÊN) ---
    with st.sidebar:
        try: st.image(LOGO_URL, use_container_width=True)
        except: st.title("🎨 4ORANGES")
        st.subheader("LAPTOP MÁY PHA MÀU")
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

    # KPI CARDS (GIỮ NGUYÊN)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TỔNG CHI PHÍ", f"{df_display['CP'].sum():,.0f} đ")
    m2.metric("SỐ CA XỬ LÝ", f"{len(df_display)} ca")
    m3.metric("TRUNG BÌNH/CA", f"{(df_display['CP'].mean() if len(df_display)>0 else 0):,.0f} đ")
    m4.metric("VÙNG CHI PHÍ CAO", df_display.groupby('VÙNG')['CP'].sum().idxmax() if not df_display.empty else "N/A")

    tabs = st.tabs(["📊 XU HƯỚNG", "💰 TÀI CHÍNH CHUYÊN SÂU", "🩺 SỨC KHỎE MÁY", "📦 KHO LOGISTICS", "🧠 AI ĐỀ XUẤT"])

    with tabs[0]: # TAB 0 GIỮ NGUYÊN
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df_display, names='VÙNG', title="CƠ CẤU CA HƯ THEO MIỀN", hole=0.4, color_discrete_sequence=ORANGE_COLORS), use_container_width=True)
        with c2:
            df_t = df_display.groupby('THÁNG').size().reset_index(name='Số ca')
            st.plotly_chart(px.line(df_t, x='THÁNG', y='Số ca', title="TỔNG CA HƯ THEO THÁNG", markers=True, color_discrete_sequence=["#FF8C00"]), use_container_width=True)

    with tabs[1]: # TAB 1 GIỮ NGUYÊN
        st.subheader("🔍 PHÂN TÍCH SÂU CHI PHÍ & TẦN SUẤT")
        deep_df = df_display.groupby('LINH_KIỆN').agg({'CP': ['sum', 'count', 'mean']}).reset_index()
        deep_df.columns = ['LINH_KIỆN', 'Tổng_CP', 'Số_lần_hỏng', 'Trung_bình_CP']
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            st.plotly_chart(px.scatter(deep_df, x="Số_lần_hỏng", y="Tổng_CP", size="Trung_bình_CP", color="LINH_KIỆN", title="MỐI TƯƠNG QUAN TẦN SUẤT VÀ TỔNG CHI PHÍ", color_discrete_sequence=px.colors.sequential.Oranges_r), use_container_width=True)
        with col_f2:
            st.write("**Gợi ý chiến lược:** Những linh kiện nằm ở góc **trên cùng bên phải** là những món cần tối ưu hợp đồng với đối tác cung cấp ngay.")
        st.plotly_chart(px.treemap(df_display, path=['VÙNG', 'LINH_KIỆN'], values='CP', title="CƠ CẤU CHI PHÍ CHI TIẾT (CAM)", color_discrete_sequence=ORANGE_COLORS), use_container_width=True)

    with tabs[2]: # TAB 2 GIỮ NGUYÊN
        health = df_f.groupby('MÃ_MÁY').agg({'NGÀY': 'count', 'CP': 'sum', 'KHÁCH': 'first', 'LINH_KIỆN': lambda x: ', '.join(set(x))}).reset_index()
        health.columns = ['Mã Máy', 'Lần hỏng', 'Tổng phí', 'Khách hàng', 'Lịch sử linh kiện']
        danger_zone = health[health['Lần hỏng'] > 2].sort_values('Lần hỏng', ascending=False)
        st.dataframe(danger_zone.style.format({"Tổng phí": "{:,.0f} đ"}), use_container_width=True)

    with tabs[3]: # TAB 3 GIỮ NGUYÊN LOGIC KHO R/OK
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
            st.plotly_chart(px.histogram(df_wh, x="VÙNG", color="TRẠNG_THÁI", barmode="group", title="ĐỐI SOÁT KHO 4ORANGES", color_discrete_map={"🟢 ĐÃ TRẢ CHI NHÁNH": "#FF8C00", "🔵 ĐANG NẰM KHO NHẬN": "#F39C12", "🟡 ĐANG SỬA NGOÀI": "#D35400", "⚪ CHỜ KIỂM TRA": "#BDC3C7"}), use_container_width=True)
            st.table(df_wh.groupby(['VÙNG', 'TRẠNG_THÁI']).size().unstack(fill_value=0))

    with tabs[4]: # --- TAB 4: NÂNG CẤP AI MODULE 1 & 2 ---
        st.subheader("🧠 TRỢ LÝ CHIẾN LƯỢC AI (MODULE 1 & 2)")
        
        # MODULE 1: PHÂN TÍCH BỆNH LÝ VÙNG MIỀN
        st.markdown("#### 📍 Module 1: Phân tích bệnh lý & Điều phối linh kiện")
        if not df_display.empty:
            vung_loi = df_display.groupby(['VÙNG', 'LINH_KIỆN']).size().reset_index(name='Số ca')
            fig_vung = px.bar(vung_loi, x='LINH_KIỆN', y='Số ca', color='VÙNG', barmode='group', title="CHI TIẾT LOẠI LỖI THEO VÙNG", color_discrete_sequence=ORANGE_COLORS)
            st.plotly_chart(fig_vung, use_container_width=True)
            
            # AI Nhận xét Module 1
            top_bac = df_display[df_display['VÙNG'].str.contains("BẮC")].groupby('LINH_KIỆN').size().idxmax() if any("BẮC" in v for v in df_display['VÙNG']) else "N/A"
            top_trung = df_display[df_display['VÙNG'].str.contains("TRUNG|ĐÀ NẴNG")].groupby('LINH_KIỆN').size().idxmax() if any(v for v in df_display['VÙNG'] if "TRUNG" in v or "ĐÀ NẴNG" in v) else "N/A"
            st.info(f"💡 **AI Tư vấn kho:** Miền Bắc hay hỏng **{top_bac}**, Miền Trung hay hỏng **{top_trung}**. Sếp nên dự phòng linh kiện theo đặc thù này để giảm thời gian chờ.")

        st.divider()

        # MODULE 2: CẢNH BÁO CHI PHÍ BẤT THƯỜNG
        st.markdown("#### ⚠️ Module 2: Cảnh báo ca sửa chữa chi phí bất thường")
        # Tính trung bình chi phí từng loại linh kiện để làm mốc so sánh
        lk_benchmark = df_f.groupby('LINH_KIỆN')['CP'].mean().reset_index(name='Gia_TB')
        df_audit = df_display.merge(lk_benchmark, on='LINH_KIỆN')
        # Tìm các ca cao hơn 1.5 lần trung bình
        anomalies = df_audit[df_audit['CP'] > df_audit['Gia_TB'] * 1.5].sort_values('CP', ascending=False)
        
        if not anomalies.empty:
            st.warning(f"Phát hiện {len(anomalies)} ca có chi phí cao bất thường (>150% so với trung bình loại linh kiện đó).")
            st.dataframe(anomalies[['NGÀY', 'MÃ_MÁY', 'LINH_KIỆN', 'CP', 'Gia_TB', 'VÙNG']].style.format({"CP": "{:,.0f}", "Gia_TB": "{:,.0f}"}))
            st.error("💡 **AI Khuyến nghị:** Sếp nên kiểm tra lại các ca trên để xác nhận thợ có 'vẽ thêm bệnh' hoặc thay linh kiện loại đắt tiền không cần thiết hay không.")
        else:
            st.success("✅ AI không phát hiện ca sửa chữa nào có chi phí bất thường trong kỳ này.")

        # Phần thanh lý cũ (Giữ lại cuối tab)
        if not danger_zone.empty:
            st.divider()
            num = max(1, int(len(danger_zone) * 0.2))
            to_liq = danger_zone.nlargest(num, 'Tổng phí')
            st.error(f"🚨 ĐỀ XUẤT THANH LÝ: {num} THIẾT BỊ NGỐN PHÍ NHẤT")
            st.table(to_liq[['Mã Máy', 'Lần hỏng', 'Tổng phí', 'Khách hàng']])

if __name__ == "__main__":
    main()
