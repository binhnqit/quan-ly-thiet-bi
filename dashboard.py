import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ Thống Sạch V3000", layout="wide")

def load_data_final():
    try:
        # Link pub của sếp
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
        # Đọc dữ liệu thô
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_records = []
        # DUYỆT TỪNG DÒNG VỚI ĐIỀU KIỆN KHẮT KHE
        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ tiêu đề
            
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach_hang = str(row.iloc[2]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # ĐIỀU KIỆN CHẾT: PHẢI CÓ MÃ MÁY VÀ PHẢI CÓ NGÀY TRÊN CÙNG DÒNG
            p_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            
            # Nếu dòng không có mã máy hoặc không có ngày hợp lệ -> LOẠI THẲNG TAY
            if not ma_may or len(ma_may) < 2 or pd.isnull(p_date):
                continue
            
            # Chỉ lấy các năm thực tế (ví dụ từ 2024 đến 2026) để tránh năm 2200 ảo
            if p_date.year < 2024 or p_date.year > 2026:
                continue

            valid_records.append({
                "NGÀY": p_date,
                "THÁNG": p_date.month,
                "NĂM": p_date.year,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": khach_hang if khach_hang else "N/A",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung_mien else ("MIỀN TRUNG" if "TRUNG" in vung_mien else "MIỀN NAM")
            })
            
        return pd.DataFrame(valid_records)
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

# --- GIAO DIỆN ---
df = load_data_final()

st.title("🛡️ HỆ THỐNG GIÁM SÁT THỰC (V3000)")

if not df.empty:
    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("TỔNG CA LỖI THẬT", len(df))
    c2.metric("SỐ MÁY HỎNG", df['MÃ_MÁY'].nunique())
    c3.metric("NĂM DỮ LIỆU", df['NĂM'].max())

    # Biểu đồ xu hướng
    st.subheader("📊 Diễn biến hỏng hóc thực tế")
    trend = df.groupby('NGÀY').size().reset_index(name='Số ca')
    fig = px.bar(trend, x='NGÀY', y='Số ca', text_auto=True, title="Số ca hỏng theo ngày")
    st.plotly_chart(fig, use_container_width=True)

    # Bảng đối soát - Cái này quan trọng nhất để sếp tin code
    st.subheader("🔍 Danh sách máy hỏng (Đối soát 1-1 với Sheets)")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ CHƯA CÓ DỮ LIỆU HỢP LỆ. Sếp lưu ý: Mỗi dòng phải có đủ 'Ngày' và 'Mã máy' thì hệ thống mới nhận.")
