import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ Thống Quản Trị V7000", layout="wide")

def load_data_exact():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    try:
        # Đọc dữ liệu không dùng header để tự định nghĩa cột
        df_raw = pd.read_csv(url, dtype=str, header=None, skiprows=3).fillna("")
        
        clean_data = []
        # Duyệt từng dòng để bóc tách đúng cột theo ảnh sếp gửi
        for _, row in df_raw.iterrows():
            ma_may = str(row.iloc[1]).strip()     # Cột B: Mã số máy
            ten_kh = str(row.iloc[2]).strip()     # Cột C: Tên KH
            ly_do = str(row.iloc[3]).strip()      # Cột D: Lý do
            chi_nhanh = str(row.iloc[5]).strip()  # Cột F: Chi nhánh
            ngay_raw = str(row.iloc[6]).strip()   # Cột G: Ngày xác nhận

            # ĐIỀU KIỆN QUYẾT ĐỊNH: Phải có Mã số máy (Master Key)
            if not ma_may or len(ma_may) < 2 or "MÃ" in ma_may.upper():
                continue

            # Xử lý ngày tháng từ cột G
            p_date = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            
            if pd.notnull(p_date):
                clean_data.append({
                    "NGÀY": p_date,
                    "NĂM": p_date.year,
                    "THÁNG": p_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": ten_kh if ten_kh else "N/A",
                    "LINH_KIỆN": ly_do if ly_do else "Chưa xác định",
                    "VÙNG": chi_nhanh if chi_nhanh else "Không xác định"
                })
        
        return pd.DataFrame(clean_data)
    except:
        return pd.DataFrame()

# --- GIAO DIỆN CHUYÊN GIA ---
df = load_data_exact()

st.title("🛡️ HỆ THỐNG PHÂN TÍCH LỖI V7000 - MASTER KEY")

if not df.empty:
    # Sidebar lọc chuẩn
    years = sorted(df['NĂM'].unique(), reverse=True)
    sel_year = st.sidebar.selectbox("📅 Chọn Năm", years)
    df_final = df[df['NĂM'] == sel_year]

    # 4 Chỉ số vàng
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Số máy hỏng", df_final['MÃ_MÁY'].nunique())
    
    re_fail = df_final['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn", len(re_fail[re_fail > 1]))
    c4.metric("Tổng khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Biểu đồ xu hướng chuyên sâu
    st.subheader(f"📈 Diễn biến hỏng hóc năm {sel_year}")
    trend = df_final.groupby('NGÀY').size().reset_index(name='Số ca')
    fig = px.area(trend, x='NGAY', y='Số ca', title="Tần suất lỗi theo thời gian")
    st.plotly_chart(fig, use_container_width=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📍 Tỷ lệ theo Chi nhánh")
        vung_fig = px.pie(df_final, names='VÙNG', hole=0.4)
        st.plotly_chart(vung_fig, use_container_width=True)
    with col_right:
        st.subheader("🔧 Top Linh kiện hỏng")
        lk_fig = px.bar(df_final['LINH_KIỆN'].value_counts().head(10), orientation='h')
        st.plotly_chart(lk_fig, use_container_width=True)

    # Bảng dữ liệu sạch hoàn toàn
    with st.expander("🔍 Xem chi tiết danh sách đã làm sạch"):
        st.dataframe(df_final, use_container_width=True)
else:
    st.error("⚠️ Không thể đọc dữ liệu. Sếp hãy kiểm tra lại cột G (Ngày) và cột B (Mã máy) đã có dữ liệu chưa?")
