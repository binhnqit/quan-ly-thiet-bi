import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi Thiết Bị", layout="wide")

@st.cache_data(ttl=1)
def load_data_v420():
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv&cache={time.time()}"
        df_raw = pd.read_csv(url, dtype=str, header=None).fillna("")
        
        valid_data = []
        last_date = pd.to_datetime("2026-01-01")

        for i, row in df_raw.iterrows():
            if i == 0: continue
            
            ma_may = str(row.iloc[1]).strip()
            # BỘ LỌC CỨNG: Chỉ dòng có Mã máy thực sự mới được điền ngày
            if not ma_may or "Mã số" in ma_may or len(ma_may) < 2:
                continue
            
            ngay_raw = str(row.iloc[0]).strip()
            dt_parse = pd.to_datetime(ngay_raw, dayfirst=True, errors='coerce')
            if pd.notnull(dt_parse):
                last_date = dt_parse
            
            valid_data.append({
                "NGÀY_DT": last_date,
                "NĂM": last_date.year,
                "THÁNG": last_date.month,
                "MÃ_MÁY": ma_may,
                "KHÁCH_HÀNG": str(row.iloc[2]).strip(),
                "LINH_KIỆN": str(row.iloc[3]).strip(),
                "VÙNG": str(row.iloc[5]).strip().upper()
            })
        return pd.DataFrame(valid_data)
    except:
        return pd.DataFrame()

df = load_data_v420()

if not df.empty:
    df['V_FIX'] = df['VÙNG'].apply(lambda x: "MIỀN BẮC" if "BẮC" in x else ("MIỀN TRUNG" if "TRUNG" in x else "MIỀN NAM"))

    with st.sidebar:
        st.markdown("### ⚙️ QUẢN TRỊ V110")
        if st.button('🔄 ĐỒNG BỘ DỮ LIỆU', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        sel_year = st.selectbox("Năm", sorted(df['NĂM'].unique(), reverse=True))
        sel_month = st.selectbox("Tháng", ["Tất cả"] + sorted(df[df['NĂM'] == sel_year]['THÁNG'].unique().tolist()))
        
        df_f = df[df['NĂM'] == sel_year]
        if sel_month != "Tất cả":
            df_f = df_f[df_f['THÁNG'] == sel_month]

    st.title("🛡️ Hệ Thống Phân Tích Lỗi Thiết Bị")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Tổng ca hỏng", len(df_f))
    with c2: st.metric("Thiết bị lỗi", df_f['MÃ_MÁY'].nunique())
    dup = df_f['MÃ_MÁY'].value_counts()
    re_f = len(dup[dup > 1])
    with c3: 
        st.metric("Hỏng tái diễn (>1)", re_f)
        if re_f > 0: st.markdown("🔴 **Cần chú trọng**")
    with c4: st.metric("Khách hàng báo lỗi", df_f['KHÁCH_HÀNG'].nunique())

    t1, t2, t3, t4 = st.tabs(["📊 XU HƯỚNG & PHÂN BỐ", "🚩 RE-FAIL", "🔍 TRUY XUẤT", "📁 DỮ LIỆU SẠCH"])

    with t1:
        cl, cr = st.columns([1.6, 1])
        with cl:
            st.subheader("📈 Xu hướng lỗi thực tế")
            trend = df_f.groupby('NGÀY_DT').size().reset_index(name='Số ca')
            fig_line = px.line(trend, x='NGÀY_DT', y='Số ca', markers=True)
            fig_line.update_traces(line_color='#1E3A8A', fill='tozeroy')
            st.plotly_chart(fig_line, use_container_width=True)
            

        with cr:
            st.subheader("📍 Tỷ lệ Vùng Miền")
            fig_pie = px.pie(df_f, names='V_FIX', hole=0.5, 
                             color_discrete_map={'MIỀN BẮC':'#34D399', 'MIỀN NAM':'#3B82F6', 'MIỀN TRUNG':'#F87171'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("🔧 Phân tích Linh kiện")
        lk = df_f['LINH_KIỆN'].value_counts().reset_index()
        fig_bar = px.bar(lk, x='count', y='LINH_KIỆN', orientation='h', text='count')
        fig_bar.update_traces(marker_color='#1E3A8A')
        st.plotly_chart(fig_bar, use_container_width=True)
        

    with t2:
        st.subheader("🚩 Thiết bị hỏng lặp lại")
        st.dataframe(dup[dup > 1], use_container_width=True)

    with t3:
        q = st.text_input("Tìm kiếm Mã máy/Khách hàng:")
        if q:
            st.dataframe(df[df['MÃ_MÁY'].str.contains(q, case=False) | df['KHÁCH_HÀNG'].str.contains(q, case=False)], use_container_width=True)

    with t4:
        st.subheader("📁 Đối soát dữ liệu")
        st.dataframe(df_f, use_container_width=True)
else:
    st.info("Hệ thống đã dọn sạch dữ liệu ảo. Đang chờ sếp nhập dữ liệu thực vào Sheets.")
