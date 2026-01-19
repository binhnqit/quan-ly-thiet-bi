import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CẤU HÌNH
st.set_page_config(page_title="Hệ Thống Quản Trị V102", layout="wide")

DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"

@st.cache_data(ttl=1)
def load_data_v102():
    try:
        url = f"{DATA_URL}&cache={time.time()}"
        # Đọc thô, không bỏ sót bất cứ thứ gì
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        final_rows = []
        for i, row in df_raw.iterrows():
            # Bỏ qua dòng tiêu đề nếu chứa chữ "Mã" hoặc "Ngày"
            row_str = " ".join(row.values.astype(str))
            if i == 0 or "Mã số" in row_str: continue
            
            # CƠ CHẾ LẤY DỮ LIỆU NỚI LỎNG (ĐẢM BẢO KHÔNG MẤT DÒNG)
            # Lấy theo vị trí cột vì sếp đã xác nhận vị trí ổn định
            ngay_raw = str(row.iloc[0]).strip()
            ma_raw = str(row.iloc[1]).strip().split('.')[0] # Xử lý trường hợp 3562.0
            kh_raw = str(row.iloc[2]).strip()
            lk_raw = str(row.iloc[3]).strip()
            
            # Nếu dòng này trống rỗng hoàn toàn thì mới bỏ
            if not ma_raw and not kh_raw: continue
            
            final_rows.append([ngay_raw, ma_raw, kh_raw, lk_raw])

        df = pd.DataFrame(final_rows, columns=['NGÀY', 'MÃ_MÁY', 'KHÁCH_HÀNG', 'LINH_KIỆN'])
        
        # Chuyển đổi ngày tháng linh hoạt
        df['NGÀY_DT'] = pd.to_datetime(df['NGÀY'], dayfirst=True, errors='coerce')
        df['NĂM'] = df['NGÀY_DT'].dt.year.fillna(2026).astype(int)
        df['THÁNG'] = df['NGÀY_DT'].dt.month.fillna(0).astype(int)
        
        # PHÂN VÙNG MIỀN (Gom nhóm sạch biểu đồ tròn)
        def classify_region(kh):
            v = str(kh).upper()
            if any(x in v for x in ['ĐÀ NẴNG', 'HUẾ', 'TRUNG', 'QUẢNG', 'VINH', 'NGHỆ', 'BÌNH ĐỊNH', 'NHA TRANG']): return 'MIỀN TRUNG'
            if any(x in v for x in ['HN', 'NỘI', 'BẮC', 'SƠN', 'PHÚ', 'THÁI', 'GIANG', 'NINH']): return 'MIỀN BẮC'
            return 'MIỀN NAM'
        
        df['VÙNG'] = df['KHÁCH_HÀNG'].apply(classify_region)
        return df
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu: {e}")
        return None

# --- APP LAYOUT ---
data = load_data_v102()

if data is not None:
    with st.sidebar:
        st.header("⚙️ ĐIỀU KHIỂN V102")
        if st.button('🔄 CẬP NHẬT DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        y_list = sorted(data['NĂM'].unique(), reverse=True)
        sel_y = st.selectbox("Năm", ["Tất cả"] + [int(y) for y in y_list if y > 2000])
        
        m_list = ["Tất cả"] + [f"Tháng {i}" for i in range(1, 13)]
        sel_m = st.selectbox("Tháng", m_list)

        # Logic lọc cực kỳ nới lỏng
        df_view = data.copy()
        if sel_y != "Tất cả": df_view = df_view[df_view['NĂM'] == sel_y]
        if sel_m != "Tất cả":
            m_num = int(sel_m.replace("Tháng ", ""))
            df_view = df_view[df_view['THÁNG'] == m_num]

    # --- HIỂN THỊ ---
    st.title(f"📊 Dashboard Tài Sản: {len(df_view)} Ca Hỏng")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", f"{len(df_view):,}")
    c2.metric("Số thiết bị lỗi", df_view['MÃ_MÁY'].nunique())
    
    re_fail = df_view['MÃ_MÁY'].value_counts()
    re_fail = re_fail[re_fail > 1]
    c3.metric("Máy hỏng tái diễn", len(re_fail))
    c4.metric("Khách hàng", df_view['KHÁCH_HÀNG'].nunique())

    t1, t2, t3 = st.tabs(["📈 BÁO CÁO CHUẨN", "⚠️ DANH SÁCH ĐEN", "📋 KIỂM TRA DỮ LIỆU"])

    with t1:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.write("**Top 10 Linh kiện lỗi**")
            top_lk = df_view['LINH_KIỆN'].value_counts().head(10)
            st.bar_chart(top_lk)
        with col_r:
            st.write("**Tỷ trọng Vùng miền**")
            fig_pie = px.pie(df_view, names='VÙNG', hole=0.4, 
                             color_discrete_map={'MIỀN BẮC':'#1E3A8A', 'MIỀN TRUNG':'#F59E0B', 'MIỀN NAM':'#10B981'})
            st.plotly_chart(fig_pie, use_container_width=True)

    with t2:
        st.subheader("🚩 THIẾT BỊ HỎNG NHIỀU LẦN")
        if not re_fail.empty:
            bl_rows = []
            for m_id, count in re_fail.items():
                if not m_id or m_id == "N/A": continue
                m_info = df_view[df_view['MÃ_MÁY'] == m_id]
                bl_rows.append({
                    "Mã Máy": m_id,
                    "Số lần hỏng": count,
                    "Khách hàng cuối": m_info['KHÁCH_HÀNG'].iloc[0],
                    "Lịch sử lỗi": " | ".join(m_info['LINH_KIỆN'].unique())
                })
            st.dataframe(pd.DataFrame(bl_rows).sort_values("Số lần hỏng", ascending=False), use_container_width=True)

    with t3:
        st.write("Dữ liệu thô đang đọc được (Nếu bảng này trống là do link Sheets lỗi):")
        st.dataframe(df_view, use_container_width=True)
