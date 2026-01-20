import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ Thống Sạch V3500", layout="wide")

def load_and_heal_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        healed_data = []
        # Biến nhớ để "điền vào chỗ trống"
        memo = {"date": None, "customer": "N/A", "region": "N/A"}

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ tiêu đề
            
            # Đọc dữ liệu thô
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach = str(row.iloc[2]).strip()
            vung = str(row.iloc[5]).strip().upper()

            # 1. LOGIC ĐIỀN TRỐNG (Cập nhật nếu có dữ liệu mới)
            temp_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            if pd.notnull(temp_date): memo["date"] = temp_date
            if khach: memo["customer"] = khach
            if vung: memo["region"] = vung

            # 2. BỘ LỌC TỬ THẦN (Chỉ lấy dòng CÓ MÃ MÁY)
            if not ma_may or len(ma_may) < 2 or "MÃ" in ma_may.upper():
                continue
            
            # 3. LƯU TRỮ (Chỉ lưu khi đã có ngày và mã máy)
            if memo["date"]:
                healed_data.append({
                    "NGÀY": memo["date"],
                    "THÁNG": memo["date"].month,
                    "NĂM": memo["date"].year,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": memo["customer"],
                    "VÙNG": "MIỀN BẮC" if "BẮC" in memo["region"] else ("MIỀN TRUNG" if "TRUNG" in memo["region"] else "MIỀN NAM")
                })
        
        return pd.DataFrame(healed_data)
    except:
        return pd.DataFrame()

# --- GIAO DIỆN ---
df = load_and_heal_data()

st.title("🛡️ GIÁM SÁT THIẾT BỊ - DỮ LIỆU ĐÃ LÀM SẠCH")

if not df.empty:
    # KPI 
    c1, c2, c3 = st.columns(3)
    c1.metric("TỔNG CA LỖI", len(df))
    c2.metric("THIẾT BỊ HỎNG", df['MÃ_MÁY'].nunique())
    c3.metric("KHÁCH HÀNG", df['KHÁCH_HÀNG'].nunique())

    # Biểu đồ xu hướng
    st.subheader("📈 Diễn biến hỏng hóc (Dữ liệu thật)")
    trend = df.groupby('NGÀY').size().reset_index(name='Số ca')
    fig = px.bar(trend, x='NGÀY', y='Số ca', text_auto=True, color_discrete_sequence=['#007AFF'])
    st.plotly_chart(fig, use_container_width=True)

    # Tab kiểm tra
    t1, t2 = st.tabs(["📁 BẢNG ĐỐI SOÁT", "📍 PHÂN BỔ VÙNG MIỀN"])
    with t1:
        st.write("Dữ liệu dưới đây đã được AI tự động điền các ô trống cho sếp:")
        st.dataframe(df.sort_values('NGÀY', ascending=False), use_container_width=True)
    with t2:
        vung_chart = px.pie(df, names='VÙNG', hole=0.4, title="Tỷ lệ lỗi theo vùng")
        st.plotly_chart(vung_chart, use_container_width=True)

else:
    st.warning("⚠️ Không tìm thấy mã máy nào. Sếp hãy kiểm tra cột B trên Sheets!")
