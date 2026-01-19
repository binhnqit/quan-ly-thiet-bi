import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- SETUP CHUẨN APPLE STYLE ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi - V1200", layout="wide")

@st.cache_data(ttl=0) # Không lưu cache lỗi, ép làm mới 100%
def load_data_professional():
    try:
        # 1. Kết nối dữ liệu
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_records = []
        anchor_date = None # Biến lưu giữ ngày tháng hiện tại

        # 2. Debug & Filter Loop
        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua header
            
            # Đọc thô và làm sạch khoảng trắng
            raw_val_date = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            khach_hang = str(row.iloc[2]).strip()
            linh_kien = str(row.iloc[3]).strip()
            vung_mien = str(row.iloc[5]).strip().upper()

            # --- BƯỚC DEBUG QUAN TRỌNG NHẤT ---
            # Chỉ cập nhật ngày tháng nếu ô đó thực sự có định dạng ngày
            new_date = pd.to_datetime(raw_val_date, dayfirst=True, errors='coerce')
            if pd.notnull(new_date):
                anchor_date = new_date

            # CHỐT CHẶN: Nếu không có Mã máy -> Dòng này vô giá trị (Rác Sheets)
            # Chúng ta không cho phép dòng trống lọt vào danh sách
            if not ma_may or "Mã số" in ma_may or len(ma_may) < 2:
                continue
            
            # CHỈ KHI CÓ MÃ MÁY VÀ ĐÃ CÓ NGÀY THÁNG THÌ MỚI LƯU
            if anchor_date:
                valid_records.append({
                    "NGÀY_DT": anchor_date,
                    "NĂM": anchor_date.year,
                    "THÁNG": anchor_date.month,
                    "MÃ_MÁY": ma_may,
                    "KHÁCH_HÀNG": khach_hang if khach_hang else "N/A",
                    "LINH_KIỆN": linh_kien if linh_kien else "Chưa ghi nhận",
                    "VÙNG": "MIỀN BẮC" if "BẮC" in vung_mien else ("MIỀN TRUNG" if "TRUNG" in vung_mien else "MIỀN NAM")
                })
        
        return pd.DataFrame(valid_records)
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        return pd.DataFrame()

# --- KHỞI CHẠY VÀ HIỂN THỊ ---
df = load_data_professional()

if not df.empty:
    # Sidebar
    with st.sidebar:
        st.markdown("### 🛡️ QUẢN TRỊ V1200")
        if st.button('🔄 ĐỒNG BỘ & LÀM SẠCH TRIỆT ĐỂ', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("📅 Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    # Dashboard chính
    st.title("📊 Hệ Thống Phân Tích Lỗi Thiết Bị")
    
    # KPI Blocks
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng (THỰC)", len(df_final))
    c2.metric("Số thiết bị", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    re_fail = len(dup[dup > 1])
    c3.metric("Hỏng tái diễn", re_fail)
    c4.metric("Khách hàng", df_final['KHÁCH_HÀNG'].nunique())

    # Tabs
    t1, t2, t3 = st.tabs(["📈 BIỂU ĐỒ XU HƯỚNG", "🚩 QUẢN TRỊ RE-FAIL", "📁 DỮ LIỆU ĐÃ LỌC"])

    with t1:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.subheader("Diễn biến hằng ngày")
            trend = df_final.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            # Cấu hình biểu đồ sạch, không bị cột đứng ảo
            fig = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig.update_traces(line_color='#007AFF', fill='tozeroy') # Apple Blue
            st.plotly_chart(fig, use_container_width=True)
            

        with col_r:
            st.subheader("Tỷ lệ Vùng Miền")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.6, 
                             color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        st.subheader("Thiết bị hỏng trên 1 lần")
        if re_fail > 0:
            st.dataframe(dup[dup > 1], use_container_width=True)
        else:
            st.success("Tình trạng thiết bị ổn định.")

    with t3:
        st.subheader("Dữ liệu gốc (Đã loại bỏ 100% dòng trống)")
        st.dataframe(df_final, use_container_width=True)

else:
    st.warning("Hệ thống đã dọn sạch rác. Vui lòng nhập dữ liệu thực vào Sheets để bắt đầu.")
