import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Hệ Thống Quản Trị AI - V41", layout="wide")

# 2. LINK CSV CỦA SẾP
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=5)
def load_data_v41():
    try:
        sync_url = f"{DATA_URL}&cache={time.time()}"
        df_raw = pd.read_csv(sync_url, on_bad_lines='skip', dtype=str)
        if df_raw.empty: return None

        df = pd.DataFrame()
        # Lấy cột 1 (Mã máy), 3 (Lý do), 6 (Ngày sửa)
        df['MÃ_MÁY'] = df_raw.iloc[:, 1].str.split('.').str[0].str.strip()
        df['LÝ_DO'] = df_raw.iloc[:, 3].fillna("Không rõ")
        
        # Xử lý ngày tháng
        df['NGAY_FIX'] = pd.to_datetime(df_raw.iloc[:, 6], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGAY_FIX'].dt.year.fillna(0).astype(int)

        # Nhận diện vùng miền
        def detect_vung(row):
            txt = " ".join(row.astype(str)).upper()
            if any(x in txt for x in ["NAM", "MN", "SG", "HCM"]): return "Miền Nam"
            if any(x in txt for x in ["BẮC", "MB", "HN"]): return "Miền Bắc"
            if any(x in txt for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Văn Phòng"
        
        df['VÙNG_MIỀN'] = df_raw.apply(detect_vung, axis=1)
        # Tạo cột search tổng hợp để tìm nhanh
        df['SEARCH_KEY'] = df['MÃ_MÁY'].astype(str) + " " + df['LÝ_DO'].astype(str) + " " + df['VÙNG_MIỀN'].astype(str)
        return df
    except Exception as e:
        return None

df_all = load_data_v41()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ ĐIỀU KHIỂN")
    if st.button('🔄 CẬP NHẬT DỮ LIỆU'):
        st.cache_data.clear()
        st.rerun()
    
    if df_all is not None:
        st.success(f"✅ Đã kết nối {len(df_all)} dòng")
        years = ["Tất cả"] + sorted([str(y) for y in df_all['NĂM'].unique() if y != 0], reverse=True)
        sel_year = st.selectbox("📅 Năm báo cáo", years)
        df_filtered = df_all if sel_year == "Tất cả" else df_all[df_all['NĂM'] == int(sel_year)]
    else:
        df_filtered = pd.DataFrame()

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h1 style="text-align: center; color: #1E3A8A;">🛡️ HỆ THỐNG QUẢN TRỊ LIVE DATA 2026</h1>', unsafe_allow_html=True)

if not df_filtered.empty:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔍 Trợ Lý Truy Lục", "🚩 Cảnh Báo", "📖 Hướng Dẫn"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng ca hỏng", f"{len(df_filtered)}")
        c2.metric("Số thiết bị", f"{df_filtered['MÃ_MÁY'].nunique()}")
        counts = df_all['MÃ_MÁY'].value_counts()
        c3.metric("Máy hỏng nặng (>4 lần)", f"{len(counts[counts >= 4])}")

        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.plotly_chart(px.pie(df_filtered, names='VÙNG_MIỀN', title="Phân bổ Khu vực", hole=0.4), use_container_width=True)
        with cr:
            def get_lk(x):
                x = str(x).lower()
                if 'pin' in x: return 'Pin'
                if 'màn' in x: return 'Màn hình'
                if 'phím' in x: return 'Bàn phím'
                if 'sạc' in x: return 'Sạc'
                return 'Khác'
            df_filtered['LK'] = df_filtered['LÝ_DO'].apply(get_lk)
            st.plotly_chart(px.bar(df_filtered['LK'].value_counts().reset_index(), x='count', y='LK', orientation='h', title="Linh kiện hỏng nhiều"), use_container_width=True)

    with tab2:
        st.subheader("💬 Trợ Lý Truy Lục Lịch Sử AI")
        # PHẦN TÌM KIẾM CẢI TIẾN CỦA SẾP ĐÂY
        q = st.text_input("Nhập bất cứ thứ gì (Mã máy, Lỗi, hoặc Khu vực):", placeholder="Ví dụ: 3534 hoặc Màn hình hoặc Miền Nam...")
        
        if q:
            # Tìm kiếm không phân biệt hoa thường trong cột search tổng hợp
            res = df_all[df_all['SEARCH_KEY'].str.contains(q, na=False, case=False)]
            
            if not res.empty:
                st.info(f"🔍 Tìm thấy {len(res)} lịch sử sửa chữa phù hợp với từ khóa '{q}'")
                # Hiển thị bảng kết quả đẹp hơn
                st.dataframe(
                    res[['NGAY_FIX', 'MÃ_MÁY', 'LÝ_DO', 'VÙNG_MIỀN']].sort_values('NGAY_FIX', ascending=False),
                    use_container_width=True,
                    column_config={
                        "NGAY_FIX": "Ngày sửa",
                        "MÃ_MÁY": "Mã thiết bị",
                        "LÝ_DO": "Chi tiết lỗi",
                        "VÙNG_MIỀN": "Khu vực"
                    }
                )
            else:
                st.error(f"❌ Không tìm thấy dữ liệu nào cho từ khóa '{q}'. Sếp thử kiểm tra lại mã máy xem sao nhé!")
        else:
            st.write("💡 *Mẹo: Sếp có thể gõ mã máy để xem máy đó đã từng hỏng những gì trong quá khứ.*")

    with tab3:
        st.subheader("🚩 Danh sách máy 'Ngốn' tiền nhất (>= 4 lần)")
        report = df_all.groupby('MÃ_MÁY').agg(Lượt_hỏng=('LÝ_DO', 'count'), Vùng=('VÙNG_MIỀN', 'first')).reset_index()
        st.table(report[report['Lượt_hỏng'] >= 4].sort_values('Lượt_hỏng', ascending=False))

    with tab4:
        st.info("📖 HƯỚNG DẪN SỬ DỤNG")
        st.markdown("""
        1. **Tra cứu nhanh:** Tại Tab 'Trợ lý Truy Lục', sếp chỉ cần gõ mã máy. AI sẽ hiện ra toàn bộ 'tiền sử bệnh án' của máy đó.
        2. **Lọc dữ liệu:** Nếu muốn xem báo cáo riêng lẻ từng năm, sếp dùng menu bên trái. Nếu muốn xem toàn bộ 3.651 dòng, chọn **'Tất cả'**.
        3. **Lưu ý:** Nếu sếp thấy ngày tháng hiện 'NaT', hãy kiểm tra lại định dạng ngày trong file Sheets (nên để Ngày/Tháng/Năm).
        """)
else:
    st.warning("⚠️ Đang chờ dữ liệu hoặc không có dữ liệu cho mục đã chọn. Sếp nhấn 'Cập nhật' ở Sidebar nhé!")
