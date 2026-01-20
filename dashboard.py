import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Phân Tích Thiết Bị V1400", layout="wide")

@st.cache_data(ttl=5) # Giữ cache ngắn để tránh lỗi 401 nhưng vẫn cập nhật nhanh
def load_data_v1400():
    try:
        # Sử dụng URL công khai chuẩn để tránh lỗi Unauthorized
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_records = []
        anchor_date = None 
        total_rows = len(df_raw)

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua tiêu đề
            
            raw_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach_hang = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # --- LOGIC XỬ LÝ NGÀY THÁNG CỰC ĐOAN ---
            # Chỉ cập nhật ngày neo nếu ô đó là ngày hợp lệ
            parsed_date = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                anchor_date = parsed_date

            # --- BỘ LỌC CHUYÊN GIA: LOẠI BỎ DÒNG RÁC ---
            # Nếu dòng không có Mã Máy hoặc chỉ có dấu cách -> BỎ QUA LUÔN
            if not ma_may or ma_may.lower() in ["mã số máy", "mã máy"] or len(ma_may) < 2:
                continue
            
            # Chỉ lưu khi dòng đó có THỰC THỂ (Mã máy) và đã có NGÀY
            if anchor_date:
                valid_records.append({
                    "NGÀY": anchor_date,
                    "NĂM": anchor_date.year,
                    "THÁNG": anchor_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": khach_hang if khach_hang else "N/A",
                    "LINH_KIỆN": linh_kien if linh_kien else "Chưa rõ",
                    "VÙNG": "BẮC" if "BẮC" in vung_mien else ("TRUNG" if "TRUNG" in vung_mien else "NAM")
                })
        
        return pd.DataFrame(valid_records), total_rows
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame(), 0

# --- THIẾT LẬP DỮ LIỆU ---
df, raw_count = load_data_v1400()

if not df.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V1400")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_year = st.selectbox("📅 Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    st.title("🛡️ Hệ Thống Giám Sát Thiết Bị")

    # KPI Sạch
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng THỰC", len(df_final))
    c2.metric("Số máy lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    c3.metric("Hỏng tái diễn", re_fail)
    c4.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Tabs
    t1, t2, t3 = st.tabs(["📊 BIỂU ĐỒ XU HƯỚNG", "🚩 CẢNH BÁO RE-FAIL", "🔍 ĐỐI SOÁT DỮ LIỆU"])

    with t1:
        st.subheader("📈 Xu hướng lỗi thực tế")
        trend = df_final.groupby('NGÀY').size().reset_index(name='Số ca')
        fig = px.line(trend, x='NGÀY', y='Số ca', markers=True, text='Số ca')
        fig.update_traces(line_color='#007AFF', fill='tozeroy', textposition="top center")
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        st.subheader("🚩 Máy hỏng nhiều lần")
        if re_fail > 0:
            st.dataframe(dup[dup > 1], use_container_width=True)
        else:
            st.success("Hệ thống ổn định.")

    with t3:
        st.subheader("📁 Nhật ký kiểm toán dữ liệu")
        col_x, col_y = st.columns(2)
        col_x.write(f"Số dòng đọc được từ Sheets: **{raw_count}**")
        col_y.write(f"Số dòng thực tế sau khi lọc: **{len(df)}**")
        st.dataframe(df_final, use_container_width=True)

else:
    st.warning("Hệ thống đã kết nối nhưng chưa thấy dữ liệu hợp lệ. Sếp hãy kiểm tra lại cột 'Mã số máy'.")
