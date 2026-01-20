import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH HỆ THỐNG CHUYÊN GIA ---
st.set_page_config(page_title="Hệ Thống Phân Tích V1500", layout="wide")

@st.cache_data(ttl=2)
def load_and_heal_data():
    try:
        # Kết nối chuẩn, ổn định
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        healed_records = []
        last_valid_date = None
        last_valid_customer = "N/A"
        last_valid_region = "CHƯA XÁC ĐỊNH"

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua Header
            
            # Đọc dữ liệu thô
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach_hang = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # --- 1. AI HEALING: TỰ ĐỘNG ĐIỀN CHỖ TRỐNG ---
            # Cập nhật ngày tháng nếu có dòng mới, nếu không dùng lại ngày cũ
            parsed_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                last_valid_date = parsed_date
            
            # Nếu có khách hàng thì nhớ, nếu không dùng lại khách hàng của máy trước đó (điền trống)
            if khach_hang: last_valid_customer = khach_hang
            if vung_mien: last_valid_region = vung_mien

            # --- 2. BỘ LỌC THỰC TẾ (CHỐT CHẶN CUỐI) ---
            # Nếu không có Mã máy thực sự -> Bỏ qua dòng này (Đây là dòng trống cuối file)
            if not ma_may or len(ma_may) < 2 or ma_may.lower() in ["mã số", "mã máy"]:
                continue
            
            # --- 3. CHỈ LƯU KHI DỮ LIỆU CÓ Ý NGHĨA ---
            if last_valid_date:
                healed_records.append({
                    "NGÀY": last_valid_date,
                    "NĂM": last_valid_date.year,
                    "THÁNG": last_valid_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": last_valid_customer,
                    "LINH_KIỆN": linh_kien if linh_kien else "Thay thế định kỳ",
                    "VÙNG": "MIỀN BẮC" if "BẮC" in last_valid_region else ("MIỀN TRUNG" if "TRUNG" in last_valid_region else "MIỀN NAM")
                })
        
        return pd.DataFrame(healed_records)
    except Exception as e:
        st.error(f"Lỗi truy xuất: {e}")
        return pd.DataFrame()

# --- XỬ LÝ DASHBOARD ---
df = load_and_heal_data()

if not df.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ DỮ LIỆU")
        if st.button('🔄 CẬP NHẬT TỨ THÌ', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_year = st.selectbox("📅 Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Chọn Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    st.title("🛡️ Hệ Thống Giám Sát Thiết Bị - V1500")

    # KPI - Số liệu đã được "Heal" và Lọc rác
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Số máy lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    c3.metric("Hỏng tái diễn", re_fail)
    c4.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Tabs chức năng
    t1, t2, t3 = st.tabs(["📊 XU HƯỚNG THỰC", "🚩 DANH SÁCH RE-FAIL", "📁 KIỂM TRA DỮ LIỆU"])

    with t1:
        st.subheader("📈 Biểu đồ xu hướng lỗi (Đã loại bỏ số ảo)")
        trend = df_final.groupby('NGÀY').size().reset_index(name='Số ca')
        fig = px.line(trend, x='NGÀY', y='Số ca', markers=True, text='Số ca')
        fig.update_traces(line_color='#007AFF', fill='tozeroy', textposition="top center")
        st.plotly_chart(fig, use_container_width=True)
        
    with t2:
        st.subheader("🚩 Các thiết bị cần chú trọng (Hỏng > 1 lần)")
        if re_fail > 0:
            st.dataframe(dup[dup > 1], use_container_width=True)
        else:
            st.success("Không phát hiện máy hỏng tái diễn trong kỳ này.")

    with t3:
        st.subheader("📁 Chi tiết bảng dữ liệu sạch")
        st.dataframe(df_final, use_container_width=True)

else:
    st.info("Hệ thống đã dọn rác thành công. Đang chờ sếp nhập dữ liệu mới vào Sheets.")
