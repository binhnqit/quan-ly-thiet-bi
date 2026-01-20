import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

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
    # --- DATA LOADING ---
    df_loi_raw = get_raw_data(URL_LAPTOP_LOI)
    df_bac_raw = get_raw_data(URL_MIEN_BAC)
    df_trung_raw = get_raw_data(URL_DA_NANG)
    df_f = process_finance_data(df_loi_raw)

    if df_f.empty:
        st.warning("⚠️ Đang chờ dữ liệu...")
        return

    # --- SIDEBAR: CẬP NHẬT CHỌN NĂM HIỆN TẠI ---
    with st.sidebar:
        try: st.image(LOGO_URL, use_container_width=True)
        except: st.title("🎨 4ORANGES")
        st.subheader("LAPTOP MÁY PHA MÀU")
        
        if st.button('🔄 LÀM MỚI DỮ LIỆU', type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        years = sorted(df_f['NĂM'].unique(), reverse=True)
        current_year = datetime.now().year
        # Nếu có năm hiện tại trong data thì chọn, không thì chọn năm mới nhất
        default_index = years.index(current_year) if current_year in years else 0
        sel_year = st.selectbox("Chọn Năm", years, index=default_index)
        
        months = ["Tất cả"] + sorted(df_f[df_f['NĂM'] == sel_year]['THÁNG'].unique().tolist())
        sel_month = st.selectbox("Chọn Tháng", months)

    # Filter dữ liệu
    df_display = df_f[df_f['NĂM'] == sel_year]
    if sel_month != "Tất cả":
        df_display = df_display[df_display['THÁNG'] == sel_month]

    st.title(f"HỆ THỐNG QUẢN LÝ LAPTOP MÁY PHA MÀU 4ORANGES - {sel_year}")
    st.divider()

    # KPI CARDS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TỔNG CHI PHÍ", f"{df_display['CP'].sum():,.0f} đ")
    m2.metric("SỐ CA XỬ LÝ", f"{len(df_display)} ca")
    m3.metric("TRUNG BÌNH/CA", f"{(df_display['CP'].mean() if len(df_display)>0 else 0):,.0f} đ")
    m4.metric("VÙNG CHI PHÍ CAO", df_display.groupby('VÙNG')['CP'].sum().idxmax() if not df_display.empty else "N/A")

    tabs = st.tabs(["📊 XU HƯỚNG", "💰 TÀI CHÍNH CHUYÊN SÂU", "🩺 SỨC KHỎE MÁY", "📦 KHO LOGISTICS", "🧠 AI ĐỀ XUẤT"])

    with tabs[1]: # TAB 1: SỬA LỖI VALUEERROR
        st.subheader("🔍 PHÂN TÍCH SÂU CHI PHÍ & TẦN SUẤT")
        deep_df = df_display.groupby('LINH_KIỆN').agg({'CP': ['sum', 'count', 'mean']}).reset_index()
        deep_df.columns = ['LINH_KIỆN', 'Tổng_CP', 'Số_lần_hỏng', 'Trung_bình_CP']
        
        # --- FIX LỖI TẠI ĐÂY ---
        # Tạo cột size an toàn: Nếu <= 0 thì gán bằng 1 để biểu đồ không lỗi
        deep_df['Size_Bong_Bong'] = deep_df['Trung_bình_CP'].apply(lambda x: max(x, 1))
        
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            try:
                st.plotly_chart(px.scatter(deep_df, x="Số_lần_hỏng", y="Tổng_CP", 
                                         size="Size_Bong_Bong", # Dùng cột size an toàn
                                         color="LINH_KIỆN", 
                                         title="MỐI TƯƠNG QUAN TẦN SUẤT VÀ TỔNG CHI PHÍ", 
                                         color_discrete_sequence=px.colors.sequential.Oranges_r), 
                                use_container_width=True)
            except:
                st.error("⚠️ Biểu đồ phân tán gặp sự cố dữ liệu. Vui lòng kiểm tra lại cột Chi Phí.")
        with col_f2:
            st.write("**Gợi ý chiến lược:** Những linh kiện nằm ở góc **trên cùng bên phải** là những món cần tối ưu hợp đồng với đối tác cung cấp ngay.")
        
        st.plotly_chart(px.treemap(df_display, path=['VÙNG', 'LINH_KIỆN'], values='CP', title="CƠ CẤU CHI PHÍ CHI TIẾT", color_discrete_sequence=ORANGE_COLORS), use_container_width=True)

    # --- CÁC TABS KHÁC GIỮ NGUYÊN LOGIC VẬN HÀNH ---
    with tabs[3]: # TAB KHO LOGISTICS
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
            st.plotly_chart(px.histogram(df_wh, x="VÙNG", color="TRẠNG_THÁI", barmode="group", title="ĐỐI SOÁT KHO 4ORANGES"), use_container_width=True)

    with tabs[4]: # TAB AI ĐỀ XUẤT (MODULE 1 & 2)
        st.subheader("🧠 TRỢ LÝ CHIẾN LƯỢC AI")
        # Logic dự báo bảo trì (Hướng 1 sếp đã chọn)
        df_p = df_f.sort_values(['MÃ_MÁY', 'NGÀY'])
        df_p['Gap'] = df_p.groupby('MÃ_MÁY')['NGÀY'].diff().dt.days
        avg_gap = df_p['Gap'].mean() if not df_p['Gap'].dropna().empty else 90
        
        st.metric("NHỊP HỎNG TB HỆ THỐNG", f"{avg_gap:.0f} Ngày")
        st.info(f"Dựa trên dữ liệu {sel_year}, AI khuyến nghị bảo trì máy định kỳ mỗi {avg_gap:.0f} ngày để tránh gián đoạn.")

if __name__ == "__main__":
    main()
