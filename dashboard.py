import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH TRỰC TIẾP ---
st.set_page_config(page_title="Hệ Thống Thực V1800", layout="wide")

# SẾP DÁN CÁI LINK TRÌNH DUYỆT CỦA FILE SHEETS VÀO ĐÂY
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GaWsUJutV4wixR3RUBZSTIMrgaD8fOIi/edit?gid=675485241#gid=675485241"

def load_data_direct():
    try:
        # Chuyển đổi link Sheets sang dạng Export để lấy dữ liệu SỐNG
        # Nếu link có dạng /edit, ta đổi thành /export
        url = SHEET_URL.replace('/edit#gid=', '/export?format=csv&gid=')
        if '/pub?output=csv' in url:
            # Nếu vẫn dùng link pub, ta thêm tham số thời gian cực mạnh để phá cache
            url += f"&refresh={pd.Timestamp.now().timestamp()}"
        
        df = pd.read_csv(url, dtype=str).fillna("")
        
        # Làm sạch dữ liệu
        clean_data = []
        last_date = None
        
        for _, row in df.iterrows():
            m_date = str(row.iloc[0]).strip()
            m_may = str(row.iloc[1]).strip()
            
            # Logic điền trống ngày tháng
            parsed_date = pd.to_datetime(m_date, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date): last_date = parsed_date
            
            # CHỈ LẤY DÒNG CÓ MÃ MÁY (Để diệt số 1736 ảo)
            if m_may and len(m_may) > 1 and last_date:
                clean_data.append({
                    "NGÀY": last_date,
                    "MÃ_MÁY": m_may,
                    "KHÁCH": row.iloc[2],
                    "VÙNG": str(row.iloc[5]).upper()
                })
        return pd.DataFrame(clean_data)
    except:
        return pd.DataFrame()

# --- HIỂN THỊ ---
df = load_data_direct()

st.title("🛡️ DỮ LIỆU THỰC TẾ (V1800)")

if not df.empty:
    c1, c2 = st.columns(2)
    c1.metric("TỔNG CA HỎNG THẬT", len(df))
    c2.metric("SỐ MÁY LỖI", df['MÃ_MÁY'].nunique())
    
    st.write("### Danh sách đối soát (Nếu bảng này sai, file Sheets chưa lưu):")
    st.dataframe(df, use_container_width=True)
    
    fig = px.histogram(df, x="NGÀY", title="Biểu đồ phân bổ ca hỏng")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Chưa đọc được dữ liệu. Sếp hãy kiểm tra lại link Sheets hoặc quyền chia sẻ (Anyone with link)!")
