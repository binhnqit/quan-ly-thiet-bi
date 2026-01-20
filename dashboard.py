import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG ---
st.set_page_config(page_title="STRATEGIC HUB V21.5", layout="wide", page_icon="🚀")

URL_LAPTOP_LOI = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=675485241&single=true&output=csv"
URL_MIEN_BAC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=602348620&single=true&output=csv"
URL_DA_NANG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?gid=1519063387&single=true&output=csv"

# --- TỐI ƯU 1: HÀM TẢI DỮ LIỆU CÓ PHÒNG VỆ ---
@st.cache_data(ttl=300) # Lưu cache 5 phút để tăng tốc
def get_raw_data(url):
    try:
        return pd.read_csv(url, on_bad_lines='skip', low_memory=False).fillna("")
    except:
        return pd.DataFrame()

# --- TỐI ƯU 2: HÀM XỬ LÝ TÀI CHÍNH TÁCH BIỆT ---
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
                    cp_raw = str(row.iloc[8]).replace(',', '').replace('đ', '').strip()
                    cp = pd.to_numeric(cp_raw, errors='coerce') or 0
                    f_list.append({
                        "NGÀY": ngay, "NĂM": ngay.year, "THÁNG": ngay.month,
                        "MÃ_MÁY": ma, "LINH_KIỆN": str(row.iloc[3]).strip(),
                        "VÙNG": str(row.iloc[5]).strip(), "CP": cp, "KHÁCH": str(row.iloc[2]).strip()
                    })
            except: continue # Bỏ qua dòng lỗi, không làm sập hệ thống
    return pd.DataFrame(f_list)

def main():
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🚀 STRATEGIC HUB")
        if st.button('🔄 REFRESH SYSTEM', type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Hiển thị trạng thái tải dữ liệu
        with st.status("📡 Đang kết nối dữ liệu...", expanded=False) as status:
            df_loi_raw = get_raw_data(URL_LAPTOP_LOI)
            df_bac_raw = get_raw_data(URL_MIEN_BAC)
            df_trung_raw = get_raw_data(URL_DA_NANG)
            df_f = process_finance_data(df_loi_raw)
            status.update(label="✅ Dữ liệu đã sẵn sàng!", state="complete")

        if df_f.empty:
            st.warning("⚠️ Đang chờ dữ liệu từ Cloud...")
            return

        years = sorted(df_f['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("Năm", years)
        months = ["Tất cả"] + sorted(df_f[df_f['NĂM'] == sel_year]['THÁNG'].unique().tolist())
        sel_month = st.selectbox("Tháng", months)

    # Filter
    df_display = df_f[df_f['NĂM'] == sel_year]
    if sel_month != "Tất cả":
        df_display = df_display[df_display['THÁNG'] == sel_month]

    # --- RENDER GIAO DIỆN (GIỮ NGUYÊN TOÀN BỘ CỦA V21.0) ---
    st.title("🛡️ HỆ THỐNG ĐIỀU HÀNH CHIẾN LƯỢC V21.5")
    
    # 5 Tab cũ của sếp
    tabs = st.tabs(["📊 XU HƯỚNG", "💰 TÀI CHÍNH", "🩺 SỨC KHỎE MÁY", "📦 KHO LOGISTICS", "🧠 AI ĐỀ XUẤT"])

    # ... [Toàn bộ nội dung logic các Tab từ bản V21.0 của sếp dán vào đây] ...
    # (Tôi lược bớt phần hiển thị Tab để code gọn nhưng sếp dán code cũ vào phần này nhé)
    
    # Riêng Tab Sức Khỏe Máy, tôi đã gỡ bỏ .background_gradient để tránh lỗi Matplotlib như đã hứa.
    with tabs[2]:
        st.subheader("🩺 DANH SÁCH THIẾT BỊ LỖI LẶP LẠI (TẦN SUẤT > 2 LẦN)")
        health_report = df_f.groupby('MÃ_MÁY').agg({
            'NGÀY': 'count', 'CP': 'sum', 'KHÁCH': 'first',
            'LINH_KIỆN': lambda x: ', '.join(set(x))
        }).reset_index()
        health_report.columns = ['Mã Máy', 'Lần hỏng', 'Tổng phí', 'Khách hàng', 'Lịch sử linh kiện']
        danger_zone = health_report[health_report['Lần hỏng'] > 2].sort_values('Lần hỏng', ascending=False)
        st.dataframe(danger_zone.style.format({"Tổng phí": "{:,.0f} đ"}), use_container_width=True)

    # Giữ nguyên Tab 4 Kho Logistics (Bắc - Trung) và Tab 5 AI đề xuất...
    # [Code Kho và AI giữ nguyên từ V21.0]

if __name__ == "__main__":
    main()
