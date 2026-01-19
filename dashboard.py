import streamlit as st
import pandas as pd
import plotly.express as px
import time
import random

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống AI 3651 Dòng - V43", layout="wide")

# LINK CSV CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=2) # Giảm thời gian nhớ xuống còn 2 giây để luôn tươi mới
def load_data_v43(url):
    try:
        # PHÁ CACHE: Thêm số ngẫu nhiên vào cuối link để ép Google đưa file mới nhất
        cache_buster = f"&update={random.randint(1000, 9999)}"
        df_raw = pd.read_csv(url + cache_buster, on_bad_lines='skip', dtype=str)
        
        if df_raw.empty: return None

        df = pd.DataFrame()
        # Lấy dữ liệu cột 1 (Mã), 3 (Lý do), 6 (Ngày) - Sếp kiểm tra lại số thứ tự cột nhé
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Không rõ")
        
        # XỬ LÝ NGÀY THÁNG SIÊU CẤP (Chấp nhận nhiều định dạng)
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], dayfirst=True, errors='coerce')
        
        # Nếu dòng nào lỗi ngày, mặc định lấy năm 2026 để sếp vẫn thấy dữ liệu
        df['NĂM'] = df['NGAY_FIX'].dt.year.fillna(2026).astype(int)
        df['THÁNG_SO'] = df['NGAY_FIX'].dt.month.fillna(1).astype(int)
        
        month_map = {1: "Tháng 1", 2: "Tháng 2", 3: "Tháng 3", 4: "Tháng 4", 5: "Tháng 5", 6: "Tháng 6",
                     7: "Tháng 7", 8: "Tháng 8", 9: "Tháng 9", 10: "Tháng 10", 11: "Tháng 11", 12: "Tháng 12"}
        df['THÁNG'] = df['THÁNG_SO'].map(month_map)

        # Nhận diện vùng miền
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG", "HCM"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        df['SEARCH_KEY'] = df['MÃ_MÁY'].astype(str) + " " + df['LÝ_DO'].astype(str)
        return df
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return None

# NÚT BẤM CẬP NHẬT TẠI SIDEBAR
with st.sidebar:
    st.header("⚙️ QUẢN TRỊ")
    if st.button('🔄 ÉP CẬP NHẬT 3.651 DÒNG'):
        st.cache_data.clear()
        st.rerun()

df_all = load_data_v43(DATA_URL)

# --- BỘ LỌC CHI TIẾT ---
if df_all is not None:
    with st.sidebar:
        st.success(f"✅ Đã kết nối {len(df_all)} dòng")
        
        # Lọc Năm
        years_list = sorted(df_all['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn Năm", ["Tất cả"] + [int(y) for y in years_list])
        
        # Lọc Tháng
        if sel_year == "Tất cả":
            df_year = df_all
        else:
            df_year = df_all[df_all['NĂM'] == sel_year]
            
        months_list = ["Tất cả"] + sorted(df_year['THÁNG'].unique().tolist(), key=lambda x: int(x.split(" ")[1]))
        sel_month = st.selectbox("📆 Chọn Tháng", months_list)
        
        # Kết quả lọc cuối cùng
        if sel_month == "Tất cả":
            df_final = df_year
        else:
            df_final = df_year[df_year['THÁNG'] == sel_month]
else:
    df_final = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_final.empty:
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Trợ Lý Truy Lục", "🚩 Cảnh Báo"])
    
    with tab1:
        st.write(f"📂 Đang hiển thị: **{sel_month} / {sel_year}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_final)}")
        c2.metric("Số thiết bị", f"{df_final['MÃ_MÁY'].nunique()}")
        counts = df_all['MÃ_MÁY'].value_counts()
        c3.metric("Máy hỏng nặng (>4 lần)", f"{len(counts[counts >= 4])}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.plotly_chart(px.pie(df_final, names='VÙNG_MIỀN', title="Khu vực", hole=0.4), use_container_width=True)
        with cr:
            st.plotly_chart(px.bar(df_final['VÙNG_MIỀN'].value_counts().reset_index(), x='count', y='VÙNG_MIỀN', color='VÙNG_MIỀN', title="Số ca theo vùng"), use_container_width=True)

    with tab2:
        st.subheader("🔍 Tìm kiếm trong 3.651 dòng")
        q = st.text_input("Nhập mã máy hoặc tên lỗi:")
        if q:
            res = df_all[df_all['SEARCH_KEY'].str.contains(q, na=False, case=False)]
            st.dataframe(res[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("🚩 Máy cần thanh lý gấp")
        bad = df_all.groupby('MÃ_MÁY').size().reset_index(name='Lượt_hỏng')
        st.table(bad[bad['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False))
else:
    st.warning("⚠️ Không tìm thấy dữ liệu. Sếp nhấn 'ÉP CẬP NHẬT' ở Sidebar nhé!")
