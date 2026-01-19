import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi V1000", layout="wide")

@st.cache_data(ttl=0)
def load_data_v1000_final():
    try:
        # Link Google Sheets của sếp
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_data = []
        ngay_gan_nhat = None 

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua header
            
            # Đọc dữ liệu thô
            raw_ngay = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach_hang = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- CHỐT CHẶN VÀNG: BỎ QUA DÒNG TRỐNG ---
            # Nếu dòng không có Mã máy thực sự -> NGỪNG XỬ LÝ DÒNG NÀY NGAY LẬP TỨC
            if not ma_may or "Mã số" in ma_may or len(ma_may) < 2:
                continue

            # --- XỬ LÝ NGÀY THÁNG THÔNG MINH ---
            # Chỉ cập nhật ngày nếu ô Ngày có dữ liệu mới
            parsed_date = pd.to_datetime(raw_ngay, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                ngay_gan_nhat = parsed_date
            
            # Gán dữ liệu vào danh sách (Nếu máy có mà ngày chưa có, lấy ngày gần nhất)
            if ngay_gan_nhat:
                valid_data.append({
                    "NGÀY_DT": ngay_gan_nhat,
                    "NĂM": ngay_gan_nhat.year,
                    "THÁNG": ngay_gan_nhat.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": khach_hang if khach_hang else "N/A",
                    "LINH_KIỆN": linh_kien if linh_kien else "Chưa ghi nhận",
                    "VÙNG": "MIỀN BẮC" if "BẮC" in vung_raw else ("MIỀN TRUNG" if "TRUNG" in vung_raw else "MIỀN NAM")
                })
        
        return pd.DataFrame(valid_data)
    except:
        return pd.DataFrame()

# --- XỬ LÝ DỮ LIỆU ---
df = load_data_v1000_final()

if not df.empty:
    # Sidebar quản trị
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V1000")
        if st.button('🔄 LÀM SẠCH & CẬP NHẬT', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("📅 Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    # Giao diện hiển thị
    st.title("🛡️ Phân Tích Lỗi Thiết Bị - Số Liệu Thực")
    
    # KPI
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng ca hỏng (THỰC)", len(df_final))
    k2.metric("Số máy lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    k3.metric("Hỏng tái diễn", re_fail)
    k4.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Tabs chức năng
    t1, t2, t3 = st.tabs(["📊 XU HƯỚNG THỰC TẾ", "🚩 CẢNH BÁO RE-FAIL", "📁 KIỂM TRA DỮ LIỆU SẠCH"])

    with t1:
        st.subheader("📈 Biểu đồ xu hướng (Đã lọc bỏ ca hỏng ảo)")
        trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
        fig = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True, 
                      title=f"Diễn biến hỏng hóc tháng {sel_month}/{sel_year}")
        fig.update_traces(line_color='#1E3A8A', fill='tozeroy')
        st.plotly_chart(fig, use_container_width=True)
        
    with t2:
        st.subheader("🚩 Các máy hỏng lặp lại trong kỳ")
        if re_fail > 0:
            st.dataframe(dup[dup > 1], use_container_width=True)
        else:
            st.success("Không có máy hỏng tái diễn.")

    with t3:
        st.subheader("📁 Danh sách chi tiết (Dữ liệu đã lọc 100% dòng trống)")
        st.dataframe(df_final, use_container_width=True)

else:
    st.error("Không tìm thấy dữ liệu máy lỗi. Sếp hãy kiểm tra lại cột 'Mã số máy' trên Google Sheets!")
