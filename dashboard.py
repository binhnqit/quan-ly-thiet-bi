import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Quản Lý Thiết Bị V9000", layout="wide")

def load_data_v9000():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    try:
        # Đọc dữ liệu thô, bỏ qua header trang trí
        df_raw = pd.read_csv(url, dtype=str, header=None, skiprows=1).fillna("")
        
        clean_data = []
        for i, row in df_raw.iterrows():
            # ÁNH XẠ CHUẨN THEO MASTER KEY (Cột B) VÀ NGÀY XÁC NHẬN (Cột G)
            ma_may = str(row.iloc[1]).strip()     # Cột B
            ten_kh = str(row.iloc[2]).strip()     # Cột C
            ly_do = str(row.iloc[3]).strip()      # Cột D
            vung_mien = str(row.iloc[5]).strip()  # Cột F
            ngay_raw = str(row.iloc[6]).strip()   # Cột G

            # Chỉ lấy dòng có Mã số máy thực sự
            if not ma_may or len(ma_may) < 2 or "MÃ" in ma_may.upper():
                continue

            # Chuyển đổi ngày
            p_date = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            
            if pd.notnull(p_date):
                clean_data.append({
                    "NGÀY": p_date,
                    "NĂM": p_date.year,
                    "THÁNG": p_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": ten_kh if ten_kh else "N/A",
                    "LINH_KIỆN": ly_do if ly_do else "Chưa xác định",
                    "VÙNG": vung_mien if vung_mien else "N/A"
                })
        return pd.DataFrame(clean_data)
    except Exception as e:
        return pd.DataFrame()

# --- KHỞI CHẠY GIAO DIỆN ---
df = load_data_v9000()

st.title("🛡️ HỆ THỐNG GIÁM SÁT THIẾT BỊ V9000")

if not df.empty:
    # Sidebar
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU'):
            st.cache_data.clear()
            st.rerun()
        
        sel_year = st.selectbox("📅 Chọn Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_year = df[df['NĂM'] == sel_year]
        
        sel_month = st.selectbox("🗓️ Chọn Tháng", ["Tất cả"] + sorted(df_year['THÁNG'].unique().tolist()))
        df_final = df_year if sel_month == "Tất cả" else df_year[df_year['THÁNG'] == sel_month]

    # HIỂN THỊ KPI (Đảm bảo biến luôn tồn tại)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng ca hỏng", len(df_final))
    col2.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    col3.metric("Hỏng tái diễn", len(dup[dup > 1]))
    col4.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # TABS CHỨC NĂNG
    tab1, tab2, tab3 = st.tabs(["📊 Biểu đồ Phân tích", "🚩 Cảnh báo Rủi ro", "📁 Dữ liệu chi tiết"])

    with tab1:
        st.subheader(f"📈 Xu hướng lỗi tháng {sel_month} năm {sel_year}")
        trend = df_final.groupby('NGÀY').size().reset_index(name='Số ca')
        if not trend.empty:
            fig_trend = px.area(trend, x='NGÀY', y='Số ca', color_discrete_sequence=['#007AFF'])
            st.plotly_chart(fig_trend, use_container_width=True)
            

        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("📍 Phân bổ theo Vùng")
            vung_data = df_final['VÙNG'].value_counts().reset_index()
            st.plotly_chart(px.pie(vung_data, values='count', names='VÙNG', hole=0.4), use_container_width=True)
        with c_right:
            st.subheader("🔧 Nguyên nhân/Linh kiện")
            lk_data = df_final['LINH_KIỆN'].value_counts().head(10).reset_index()
            st.plotly_chart(px.bar(lk_data, x='count', y='LINH_KIỆN', orientation='h', text_auto=True), use_container_width=True)

    with tab2:
        if len(dup[dup > 1]) > 0:
            st.error("DANH SÁCH MÁY HỎNG NHIỀU LẦN")
            st.dataframe(dup[dup > 1], use_container_width=True)
        else:
            st.success("Hệ thống vận hành ổn định, không có máy hỏng tái diễn.")

    with tab3:
        st.write("Bảng dữ liệu đã đối soát sạch:")
        st.dataframe(df_final, use_container_width=True)

else:
    st.info("Hệ thống đang chờ dữ liệu sạch từ Google Sheets (Cần cột B và cột G).")
