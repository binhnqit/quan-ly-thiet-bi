import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- SETUP GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi V1700", layout="wide")

@st.cache_data(ttl=1) # Cache cực ngắn để cập nhật liên tục
def load_data_expert():
    try:
        # Sử dụng lại URL CSV công khai mà sếp đã share (Đã test kết nối OK)
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
        
        # Thêm tham số cache buster đơn giản để ép Google không dùng bản cũ
        full_url = f"{url}&refresh={int(time.time())}"
        df_raw = pd.read_csv(full_url, dtype=str, header=None).fillna("")
        
        valid_rows = []
        last_date = None
        total_raw = len(df_raw)

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ tiêu đề
            
            # Đọc cột
            c_date = str(row.iloc[0]).strip()
            c_may = str(row.iloc[1]).strip()
            c_kh = str(row.iloc[2]).strip()
            c_lk = str(row.iloc[3]).strip()
            c_vung = str(row.iloc[5]).strip().upper()

            # 1. Cập nhật ngày tháng (Logic Điền chỗ trống)
            # Nếu sếp nhập ngày ở dòng trên, các dòng dưới để trống vẫn được tính vào ngày đó
            parsed = pd.to_datetime(c_date, dayfirst=True, errors='coerce')
            if pd.notnull(parsed):
                last_date = parsed

            # 2. CHỐT CHẶN RÁC (Quyết định số liệu đúng/sai ở đây)
            # Chỉ lấy dòng nếu có Mã máy (ít nhất 2 ký tự)
            if not c_may or len(c_may) < 2 or "MÃ" in c_may.upper():
                continue
            
            # 3. Ghi nhận nếu đã có ngày và có máy
            if last_date:
                valid_rows.append({
                    "NGÀY": last_date,
                    "NĂM": last_date.year,
                    "THÁNG": last_date.month,
                    "MÃ_MÁY": c_may,
                    "KHÁCH_HÀNG": c_kh if c_kh else "N/A",
                    "LINH_KIỆN": c_lk if c_lk else "Chưa rõ",
                    "VÙNG": "MIỀN BẮC" if "BẮC" in c_vung else ("MIỀN TRUNG" if "TRUNG" in c_vung else "MIỀN NAM")
                })
        
        return pd.DataFrame(valid_rows), total_raw
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return pd.DataFrame(), 0

# --- THI ĐẶT DASHBOARD ---
df, raw_count = load_data_expert()

if not df.empty:
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ DỮ LIỆU")
        if st.button('🔄 ĐỒNG BỘ NGAY LẬP TỨC', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_year = st.selectbox("📅 Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    st.title("🛡️ Dashboard Phân Tích Lỗi Thiết Bị")

    # --- BẢNG SỨC KHỎE DỮ LIỆU (DEBUG ĐỂ SẾP KIỂM TRA) ---
    with st.expander("🔍 KIỂM TOÁN DỮ LIỆU (Dành cho sếp kiểm tra lỗi số ảo)"):
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Tổng dòng Sheets đọc được", raw_count)
        col_b.metric("Số dòng Mã máy hợp lệ", len(df))
        col_c.write("Mẹo: Nếu số dòng hợp lệ ít hơn sếp nghĩ, hãy kiểm tra lại cột B trên Sheets.")

    # KPI Sạch
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    c3.metric("Hỏng tái diễn", re_fail)
    c4.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Tabs
    t1, t2, t3 = st.tabs(["📊 BIỂU ĐỒ XU HƯỚNG", "🚩 QUẢN TRỊ RỦI RO", "📁 CHI TIẾT DỮ LIỆU SẠCH"])

    with t1:
        st.subheader("📈 Xu hướng lỗi thực tế")
        trend = df_final.groupby('NGÀY').size().reset_index(name='Số ca')
        fig = px.line(trend, x='NGÀY', y='Số ca', markers=True, text='Số ca')
        fig.update_traces(line_color='#007AFF', fill='tozeroy', textposition="top center")
        st.plotly_chart(fig, use_container_width=True)
        

    with t2:
        st.subheader("🚩 Máy hỏng nhiều lần (Re-fail)")
        if re_fail > 0:
            st.dataframe(dup[dup > 1], use_container_width=True)
        else:
            st.success("Tình trạng thiết bị ổn định.")

    with t3:
        st.subheader("📁 Bảng đối soát dòng dữ liệu")
        st.dataframe(df_final, use_container_width=True)

else:
    st.warning("⚠️ Đã kết nối nhưng không tìm thấy dữ liệu máy lỗi. Sếp hãy kiểm tra cột 'Mã số máy'!")
