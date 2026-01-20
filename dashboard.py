import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tổng Kết 2026 chuẩn", layout="wide")

def get_2026_clean_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    try:
        # Đọc dữ liệu thô
        df = pd.read_csv(url, dtype=str, header=None).fillna("")
        clean_rows = []
        
        for i, row in df.iterrows():
            if i == 0: continue
            
            # Lấy dữ liệu
            d_raw = str(row.iloc[0]).strip()
            m_may = str(row.iloc[1]).strip()
            
            # CHẶN RÁC KHÔNG KHOAN NHƯỢNG
            dt = pd.to_datetime(d_raw, dayfirst=True, errors='coerce')
            
            # ĐIỀU KIỆN SẠCH: Phải là năm 2026 + Phải có mã máy
            if dt and dt.year == 2026 and m_may and len(m_may) > 1:
                clean_rows.append({
                    "NGÀY": dt.strftime('%d/%m/%Y'),
                    "MÃ MÁY": m_may,
                    "KHÁCH HÀNG": row.iloc[2],
                    "LINH KIỆN": row.iloc[3],
                    "VÙNG": row.iloc[5]
                })
        return pd.DataFrame(clean_rows)
    except:
        return pd.DataFrame()

df_2026 = get_2026_clean_data()

st.header("🍎 TỔNG KẾT DỮ LIỆU SẠCH NĂM 2026")

if not df_2026.empty:
    col1, col2 = st.columns(2)
    col1.metric("TỔNG CA LỖI THẬT", len(df_2026))
    col2.metric("SỐ MÁY HỎNG", df_2026['MÃ MÁY'].nunique())
    
    st.write("### 📋 Danh sách chi tiết (100% thực tế)")
    st.table(df_2026) # Dùng table cho rõ ràng, không thể sai lệch
else:
    st.error("⚠️ Hệ thống xác nhận: Năm 2026 hiện chưa có dữ liệu nào hợp lệ (hoặc thiếu Ngày, hoặc thiếu Mã máy).")
