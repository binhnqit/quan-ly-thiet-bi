import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH HỆ THỐNG V2000 ---
st.set_page_config(page_title="Hệ Thống Live Data V2000", layout="wide")

def get_clean_url(url):
    # Tự động chuyển đổi các loại link Sheets về định dạng Export CSV
    if "/edit" in url:
        return url.split("/edit")[0] + "/export?format=csv&gid=0"
    if "pub?output=csv" in url:
        return url + f"&cachebuster={int(time.time())}"
    return url

# Link hiện tại của sếp
SHEET_LINK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_expert_v2():
    try:
        final_url = get_clean_url(SHEET_LINK)
        # Đọc dữ liệu thô, không lấy Header để tránh lỗi lệch cột
        df_raw = pd.read_csv(final_url, dtype=str, header=None).fillna("")
        
        valid_rows = []
        # Biến nhớ để "Điền vào chỗ trống"
        memo = {"ngay": None, "khach": "N/A", "vung": "N/A"}

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua dòng tiêu đề của Sheets
            
            # Đọc giá trị từng cột
            val_date = str(row.iloc[0]).strip()
            val_may = str(row.iloc[1]).strip()
            val_kh = str(row.iloc[2]).strip()
            val_vung = str(row.iloc[5]).strip().upper()

            # 1. LOGIC ĐIỀN TRỐNG (DATA HEALING)
            # Cập nhật Ngày nếu có, không thì dùng ngày dòng trước
            d_parsed = pd.to_datetime(val_date, dayfirst=True, errors='coerce')
            if pd.notnull(d_parsed): memo["ngay"] = d_parsed
            
            # Cập nhật Khách/Vùng nếu có
            if val_kh: memo["khach"] = val_kh
            if val_vung: memo["vung"] = val_vung

            # 2. CHỐT CHẶN RÁC (BỨC PHÁ)
            # Chỉ lưu nếu dòng này CÓ MÃ MÁY thực sự
            if val_may and len(val_may) > 1 and "MÃ" not in val_may.upper():
                if memo["ngay"]:
                    valid_rows.append({
                        "NGÀY": memo["ngay"],
                        "NĂM": memo["ngay"].year,
                        "THÁNG": memo["ngay"].month,
                        "MÃ_MÁY": val_may,
                        "KHÁCH_HÀNG": memo["khach"],
                        "VÙNG": "BẮC" if "BẮC" in memo["vung"] else ("TRUNG" if "TRUNG" in memo["vung"] else "NAM")
                    })
        
        return pd.DataFrame(valid_rows), len(df_raw)
    except Exception as e:
        st.error(f"Lỗi kết nối trực tiếp: {e}")
        return pd.DataFrame(), 0

# --- HIỂN THỊ ---
df, total_read = load_data_expert_v2()

st.title("🛡️ Dashboard Quản Trị Lỗi - Live V2000")

if not df.empty:
    # Sidebar lọc
    with st.sidebar:
        if st.button('🔄 LÀM MỚI DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        sel_month = st.selectbox("Chọn Tháng", ["Tất cả"] + sorted(df['THÁNG'].unique().tolist()))
        
    df_view = df if sel_month == "Tất cả" else df[df['THÁNG'] == sel_month]

    # KPI Sạch
    c1, c2, c3 = st.columns(3)
    c1.metric("TỔNG CA LỖI THỰC", len(df_view))
    c2.metric("SỐ THIẾT BỊ HỎNG", df_view['MÃ_MÁY'].nunique())
    c3.metric("DÒNG RÁC ĐÃ LOẠI", total_read - len(df))

    # Tabs
    t1, t2 = st.tabs(["📊 BIỂU ĐỒ XU HƯỚNG", "📁 DỮ LIỆU ĐỐI SOÁT"])
    with t1:
        trend = df_view.groupby('NGÀY').size().reset_index(name='Số ca')
        fig = px.line(trend, x='NGÀY', y='Số ca', markers=True, title="Xu hướng lỗi hằng ngày")
        fig.update_traces(line_color='#007AFF', fill='tozeroy')
        st.plotly_chart(fig, use_container_width=True)
        

    with t2:
        st.write("Dữ liệu Python đã 'điền vào chỗ trống' thành công:")
        st.dataframe(df_view, use_container_width=True)
else:
    st.error("❌ Hệ thống vẫn không thấy dữ liệu.")
    st.info("Sếp hãy kiểm tra 1 việc duy nhất: Mở file Sheets, chọn File -> Share -> Anyone with the link can VIEW.")
