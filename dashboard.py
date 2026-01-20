import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Phân Tích Thực - V1600", layout="wide")

def get_google_sheet_url():
    # Chuyển đổi link "pubhtml" sang link "export?format=csv" để lấy dữ liệu tươi nhất
    base_url = "https://docs.google.com/spreadsheets/d/1-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg"
    return f"{base_url}/export?format=csv&gid=0"

def load_data_realtime():
    try:
        # Đọc trực tiếp từ API export của Google
        url = get_google_sheet_url()
        df_raw = pd.read_csv(url, dtype=str).fillna("")
        
        # Làm sạch tên cột (Tránh lỗi do sếp đổi tên cột trên Sheets)
        df_raw.columns = [str(c).strip().upper() for c in df_raw.columns]
        
        # Map lại các cột theo vị trí để chính xác tuyệt đối
        # Cột 0: Ngày, Cột 1: Mã máy, Cột 2: Khách hàng, Cột 3: Linh kiện, Cột 5: Vùng
        processed = []
        current_date = None
        
        for _, row in df_raw.iterrows():
            r_date = str(row.iloc[0]).strip()
            r_may = str(row.iloc[1]).strip()
            r_kh = str(row.iloc[2]).strip()
            r_lk = str(row.iloc[3]).strip()
            r_vung = str(row.iloc[5]).strip().upper()

            # 1. Logic Điền chỗ trống (Heal Data)
            p_date = pd.to_datetime(r_date, dayfirst=True, errors='coerce')
            if pd.notnull(p_date):
                current_date = p_date

            # 2. CHỐT CHẶN RÁC: Nếu không có mã máy thực sự -> Bỏ qua
            if not r_may or len(r_may) < 2 or "MÃ" in r_may.upper():
                continue
            
            if current_date:
                processed.append({
                    "NGÀY_DT": current_date,
                    "NĂM": current_date.year,
                    "THÁNG": current_date.month,
                    "MÃ_MÁY": r_may,
                    "KHÁCH_HÀNG": r_kh if r_kh else "N/A",
                    "LINH_KIỆN": r_lk if r_lk else "Chưa rõ",
                    "VÙNG": "MIỀN BẮC" if "BẮC" in r_vung else ("MIỀN TRUNG" if "TRUNG" in r_vung else "MIỀN NAM")
                })
        
        return pd.DataFrame(processed)
    except Exception as e:
        st.error(f"Lỗi kết nối trực tiếp: {e}")
        return pd.DataFrame()

# --- GIAO DIỆN ---
df = load_data_realtime()

if not df.empty:
    with st.sidebar:
        st.header("⚙️ HỆ THỐNG V1600")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU TƯƠI', use_container_width=True):
            st.rerun()
        
        sel_year = st.selectbox("📅 Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    st.title("🛡️ Dashboard Phân Tích Lỗi Thực Tế")
    
    # KPI 
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Số máy lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    c3.metric("Hỏng tái diễn", re_fail)
    c4.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Tab kiểm tra dữ liệu - Để sếp thấy Python KHÔNG ĐỌC SAI
    t1, t2 = st.tabs(["📊 BIỂU ĐỒ", "🔍 KIỂM TRA DÒNG DỮ LIỆU"])
    
    with t1:
        trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
        fig = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True, title="Xu hướng hỏng hóc thực tế")
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        st.write("Dữ liệu Python đang đọc được (Nếu bảng này trống hoặc sai, lỗi tại Google Sheets chưa lưu):")
        st.dataframe(df_final, use_container_width=True)
else:
    st.warning("⚠️ Không tìm thấy dữ liệu. Sếp hãy kiểm tra lại file Sheets đã có Mã máy chưa?")
