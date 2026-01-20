import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. CONFIG ---
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
    # Load dữ liệu gốc
    df_loi_raw = get_raw_data(URL_LAPTOP_LOI)
    df_bac_raw = get_raw_data(URL_MIEN_BAC)
    df_trung_raw = get_raw_data(URL_DA_NANG)
    df_f = process_finance_data(df_loi_raw)

    if df_f.empty:
        st.warning("⚠️ Đang kết nối dữ liệu...")
        return

    # --- SIDEBAR: CHỌN NĂM HIỆN TẠI ---
    with st.sidebar:
        st.title("🎨 4ORANGES AI")
        if st.button('🔄 LÀM MỚI DỮ LIỆU', type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        years = sorted(df_f['NĂM'].unique(), reverse=True)
        current_year = datetime.now().year
        default_idx = years.index(current_year) if current_year in years else 0
        sel_year = st.selectbox("Chọn Năm", years, index=default_idx)
        
        months = ["Tất cả"] + sorted(df_f[df_f['NĂM'] == sel_year]['THÁNG'].unique().tolist())
        sel_month = st.selectbox("Chọn Tháng", months)

    # Lọc dữ liệu hiển thị
    df_display = df_f[df_f['NĂM'] == sel_year]
    if sel_month != "Tất cả":
        df_display = df_display[df_display['THÁNG'] == sel_month]

    st.header(f"QUẢN LÝ LAPTOP MÁY PHA MÀU - DỮ LIỆU {sel_year}")
    
    # KPI TOP
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TỔNG CHI PHÍ", f"{df_display['CP'].sum():,.0f} đ")
    k2.metric("SỐ CA HƯ", f"{len(df_display)} ca")
    k3.metric("TRUNG BÌNH/CA", f"{(df_display['CP'].mean() if len(df_display)>0 else 0):,.0f} đ")
    k4.metric("VÙNG CHI PHÍ CAO", df_display.groupby('VÙNG')['CP'].sum().idxmax() if not df_display.empty else "N/A")

    # --- HỆ THỐNG TAB (KHÔI PHỤC ĐẦY ĐỦ) ---
    t = st.tabs(["📊 XU HƯỚNG", "💰 TÀI CHÍNH", "🩺 SỨC KHỎE", "📦 KHO", "🧠 AI CTO"])

    with t[0]: # XU HƯỚNG
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_display, names='VÙNG', title="CƠ CẤU THEO MIỀN", hole=0.4, color_discrete_sequence=ORANGE_COLORS), use_container_width=True)
        with c2: 
            df_line = df_display.groupby('THÁNG').size().reset_index(name='Ca')
            st.plotly_chart(px.line(df_line, x='THÁNG', y='Ca', title="BIẾN ĐỘNG THEO THÁNG", markers=True), use_container_width=True)

    with t[1]: # TÀI CHÍNH (FIX LỖI 2023)
        st.subheader("PHÂN TÍCH TƯƠNG QUAN CHI PHÍ")
        deep_df = df_display.groupby('LINH_KIỆN').agg({'CP': ['sum', 'count', 'mean']}).reset_index()
        deep_df.columns = ['LINH_KIỆN', 'Tổng_CP', 'Số_lần_hỏng', 'Trung_bình_CP']
        # Fix: Đảm bảo size > 0 để Plotly không crash
        deep_df['Size_Safe'] = deep_df['Trung_bình_CP'].apply(lambda x: max(x, 1))
        
        st.plotly_chart(px.scatter(deep_df, x="Số_lần_hỏng", y="Tổng_CP", size="Size_Safe", color="LINH_KIỆN", title="TẦN SUẤT vs CHI PHÍ"), use_container_width=True)
        st.plotly_chart(px.treemap(df_display, path=['VÙNG', 'LINH_KIỆN'], values='CP', title="PHÂN BỔ CHI PHÍ", color_discrete_sequence=ORANGE_COLORS), use_container_width=True)

    with t[2]: # SỨC KHỎE
        health = df_f.groupby('MÃ_MÁY').agg({'NGÀY': 'count', 'CP': 'sum', 'KHÁCH': 'first', 'LINH_KIỆN': lambda x: ', '.join(set(x))}).reset_index()
        health.columns = ['Mã Máy', 'Lần hỏng', 'Tổng phí', 'Khách hàng', 'Linh kiện']
        st.dataframe(health[health['Lần hỏng'] > 1].sort_values('Lần hỏng', ascending=False), use_container_width=True)

    with t[3]: # KHO LOGISTICS
        wh_data = []
        for reg, raw in [("BẮC", df_bac_raw), ("TRUNG", df_trung_raw)]:
            if not raw.empty:
                for _, r in raw.iloc[1:].iterrows():
                    m_id = str(r.iloc[1]).strip()
                    if not m_id: continue
                    st_nb, st_ng, st_giao = (str(r.iloc[6])+str(r.iloc[8])).upper(), (str(r.iloc[9])+str(r.iloc[11])).upper(), str(r.iloc[13]).upper()
                    if "R" in st_giao: tt = "🟢 ĐÃ TRẢ"
                    elif "OK" in st_nb: tt = "🔵 TẠI KHO"
                    elif any(x in st_ng for x in ["OK", "SỬA"]): tt = "🟡 ĐANG SỬA"
                    else: tt = "⚪ CHỜ KIỂM"
                    wh_data.append({"VÙNG": reg, "TRẠNG_THÁI": tt})
        if wh_data:
            st.plotly_chart(px.histogram(pd.DataFrame(wh_data), x="VÙNG", color="TRẠNG_THÁI", barmode="group", title="TRẠNG THÁI MÁY TRONG KHO"), use_container_width=True)

    with t[4]: # AI CTO (DỰ BÁO)
        st.subheader("🧠 DỰ BÁO BẢO TRÌ & KIỂM TOÁN AI")
        df_p = df_f.sort_values(['MÃ_MÁY', 'NGÀY'])
        df_p['Gap'] = df_p.groupby('MÃ_MÁY')['NGÀY'].diff().dt.days
        avg_gap = df_p['Gap'].mean() if not df_p['Gap'].dropna().empty else 90
        
        c1, c2 = st.columns(2)
        c1.metric("NHỊP HỎNG TB", f"{avg_gap:.0f} Ngày")
        
        # Cảnh báo chi phí (Module 2)
        lk_avg = df_f.groupby('LINH_KIỆN')['CP'].mean().reset_index(name='Avg')
        df_audit = df_display.merge(lk_avg, on='LINH_KIỆN')
        anom = df_audit[df_audit['CP'] > df_audit['Avg'] * 1.5]
        if not anom.empty:
            st.warning(f"Phát hiện {len(anom)} ca bất thường!")
            st.dataframe(anom[['MÃ_MÁY', 'LINH_KIỆN', 'CP', 'Avg']])

if __name__ == "__main__":
    main()
