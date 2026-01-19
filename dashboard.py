import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH PRO V110 ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=1)
def load_data_v850():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_rows = []
        current_date_anchor = None # Ngày neo để kế thừa

        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ qua dòng tiêu đề gốc của Sheets
            
            # 1. Trích xuất dữ liệu thô
            raw_ngay = str(row.iloc[0]).strip()
            ma_may = str(row.iloc[1]).strip()
            ten_kh = str(row.iloc[2]).strip()
            lk_hong = str(row.iloc[3]).strip()
            vung_raw = str(row.iloc[5]).strip().upper()

            # --- 2. GIẢI PHÁP BỨC PHÁ: LỌC DỮ LIỆU THỰC ---
            # Chốt chặn: Nếu không có Mã máy, hoặc Mã máy là tiêu đề rác -> BỎ QUA NGAY
            if not ma_may or "Mã số" in ma_may or "Mã máy" in ma_may or len(ma_may) < 2:
                continue

            # --- 3. XỬ LÝ NGÀY THÁNG CHUẨN XÁC ---
            # Chỉ cập nhật ngày neo nếu ô ngày có dữ liệu mới hợp lệ
            parsed_date = pd.to_datetime(raw_ngay, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date):
                current_date_anchor = parsed_date
            
            # Nếu dòng có Mã máy nhưng vẫn chưa có ngày neo (dòng đầu tiên lỗi), mặc định 01/01/2026
            final_date = current_date_anchor if current_date_anchor else pd.to_datetime("2026-01-01")

            # 4. Lưu trữ dữ liệu sạch
            valid_rows.append({
                "DATE_OBJ": final_date,
                "NĂM": final_date.year,
                "THÁNG": final_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": ten_kh if ten_kh else "Khách vãng lai",
                "LINH_KIỆN": lk_hong if lk_hong else "N/A",
                "VÙNG": "MIỀN BẮC" if "BẮC" in vung_raw else ("MIỀN TRUNG" if "TRUNG" in vung_raw else "MIỀN NAM")
            })
        
        return pd.DataFrame(valid_rows)
    except:
        return pd.DataFrame()

# --- KHỞI CHẠY HỆ THỐNG ---
df = load_data_v850()

if not df.empty:
    with st.sidebar:
        st.markdown("### 🛠️ QUẢN TRỊ V110")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU THỰC', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_year = st.selectbox("📅 Năm", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.selectbox("🗓️ Tháng", ["Tất cả"] + sorted(df_y['THÁNG'].unique().tolist()))
        
        df_final = df_y if sel_month == "Tất cả" else df_y[df_y['THÁNG'] == sel_month]

    # --- HEADER KPI ---
    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1: st.metric("Tổng ca hỏng", len(df_final))
    with kpi2: st.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup_counts = df_final['MÃ_MÁY'].value_counts()
    refail = len(dup_counts[dup_counts > 1])
    with kpi3: 
        st.metric("Hỏng tái diễn (>1)", refail)
        if refail > 0: st.error("⚠️ Cảnh báo Re-fail")
    with kpi4: st.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

    # --- TABS CHỨC NĂNG (THEO HÌNH SẾP DUYỆT) ---
    t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG & VÙNG MIỀN", "🚩 QUẢN TRỊ RỦI RO", "🔍 TRUY XUẤT", "📁 DỮ LIỆU SẠCH"])

    with t1:
        c_left, c_right = st.columns([1.6, 1])
        with c_left:
            st.subheader("📈 Xu hướng lỗi thực tế")
            trend_df = df_final.groupby('DATE_OBJ').size().reset_index(name='Số ca')
            fig_line = px.line(trend_df, x='DATE_OBJ', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#003366', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)
            

        with c_right:
            st.subheader("📍 Phân bổ Vùng Miền")
            fig_pie = px.pie(df_final, names='VÙNG', hole=0.5, 
                             color_discrete_map={'MIỀN BẮC':'#34D399', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#F87171'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("🔧 Phân tích Linh kiện")
        lk_df = df_final['LINH_KIỆN'].value_counts().reset_index()
        fig_bar = px.bar(lk_df, x='count', y='LINH_KIỆN', orientation='h', text='count')
        fig_bar.update_traces(marker_color='#003366')
        st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.subheader("🚩 Danh sách thiết bị báo động (Hỏng từ 2 lần trở lên)")
        if refail > 0:
            st.dataframe(dup_counts[dup_counts > 1], use_container_width=True)
        else:
            st.success("Không có máy hỏng tái diễn trong tháng này.")

    with t3:
        search = st.text_input("🔍 Tra cứu Mã máy hoặc Khách hàng:")
        if search:
            st.dataframe(df[df['MÃ_MÁY'].str.contains(search, case=False) | df['KHÁCH_HÀNG'].str.contains(search, case=False)], use_container_width=True)

    with t4:
        st.subheader("📁 Đối soát dòng dữ liệu thực tế (Đã làm sạch rác)")
        st.dataframe(df_final, use_container_width=True)

else:
    st.warning("Hệ thống đã loại bỏ 100% dòng ảo. Sếp hãy nhập dữ liệu thực tế vào Sheets để hiển thị!")
