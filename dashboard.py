import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Quản Trị V16.1", layout="wide")

# --- 2. HÀM ĐỌC DỮ LIỆU FILE 1 (LỊCH SỬ - GỐC) ---
@st.cache_data(ttl=2)
def load_data_history():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    try:
        df_raw = pd.read_csv(url, dtype=str, header=None, skiprows=1).fillna("0")
        clean_data = []
        for i, row in df_raw.iterrows():
            ma_may = str(row.iloc[1]).strip()
            if not ma_may or len(ma_may) < 2 or "MÃ" in ma_may.upper(): continue
            p_date = pd.to_datetime(str(row.iloc[6]).strip(), dayfirst=True, errors='coerce')
            if pd.notnull(p_date):
                cp_dk = pd.to_numeric(str(row.iloc[7]).replace(',', ''), errors='coerce') or 0
                cp_tt = pd.to_numeric(str(row.iloc[8]).replace(',', ''), errors='coerce') or 0
                clean_data.append({
                    "NGÀY": p_date, "NĂM": p_date.year, "THÁNG": p_date.month,
                    "MÃ_MÁY": ma_may, "KHÁCH_HÀNG": str(row.iloc[2]).strip(),
                    "LINH_KIỆN": str(row.iloc[3]).strip(), "VÙNG": str(row.iloc[5]).strip(),
                    "CP_DU_KIEN": cp_dk, "CP_THUC_TE": cp_tt, "CHENH_LECH": cp_tt - cp_dk
                })
        return pd.DataFrame(clean_data)
    except: return pd.DataFrame()

# --- 3. HÀM ĐỌC DỮ LIỆU FILE 2 (KHO 2 CHI NHÁNH) ---
@st.cache_data(ttl=2)
def load_data_warehouse():
    sheet_id = "1GaWsUJutV4wixR3RUBZSTIMrgaD8fOIi"
    urls = {
        "ĐÀ NẴNG": f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=602348620",
        "MIỀN BẮC": f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1626219342"
    }
    all_data = []
    for branch, url in urls.items():
        try:
            df_temp = pd.read_csv(url).fillna("")
            df_temp.columns = [c.strip().upper() for c in df_temp.columns]
            for _, row in df_temp.iterrows():
                ma_may = str(row.get('MÃ SỐ MÁY', '')).strip()
                if not ma_may or len(ma_may) < 2: continue
                
                d_nhan = pd.to_datetime(row.get('NGÀY NHẬN', ''), dayfirst=True, errors='coerce')
                d_tra = pd.to_datetime(row.get('NGÀY TRẢ', ''), dayfirst=True, errors='coerce')
                sua_nb = str(row.get('SỬA NỘI BỘ', '')).upper()
                hu_ko_sua = str(row.get('HƯ KHÔNG SỬA ĐƯỢC', '')).strip()

                status = "🟢 ĐÃ TRẢ/XONG" if pd.notnull(d_tra) or "OK" in str(row.get('GIAO LẠI ĐN', '')).upper() else "🟡 ĐANG XỬ LÝ"
                if "THANH LÝ" in sua_nb or hu_ko_sua != "": status = "🔴 THANH LÝ/HỦY"

                all_data.append({
                    "CHI NHÁNH": branch, "MÃ MÁY": ma_may, "NGÀY NHẬN": d_nhan,
                    "NGÀY TRẢ": d_tra, "TRẠNG THÁI": status, "LOẠI MÁY": row.get('LOẠI MÁY', ''),
                    "SỬA NGOÀI": row.get('SỬA BÊN NGOÀI', ''), "KIỂM TRA": row.get('KIỂM TRA THỰC TẾ', '')
                })
        except: continue
    return pd.DataFrame(all_data)

# --- 4. KHỞI CHẠY DỮ LIỆU ---
df_hist = load_data_history()
df_ware = load_data_warehouse()

if not df_hist.empty:
    # SIDEBAR QUẢN TRỊ (CHUNG CHO FILE 1)
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3208/3208726.png", width=80)
        st.title("EXECUTIVE HUB V16.1")
        if st.button('🔄 ĐỒNG BỘ TOÀN HỆ THỐNG'):
            st.cache_data.clear()
            st.rerun()
        
        all_years = sorted(df_hist['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Chọn năm báo cáo", all_years)
        df_y = df_hist[df_hist['NĂM'] == sel_year]
        
        all_months = sorted(df_y['THÁNG'].unique())
        sel_month = st.multiselect("🗓️ Lọc Tháng", all_months, default=all_months)
        df_final = df_y[df_y['THÁNG'].isin(sel_month)]

        st.write("---")
        csv = df_final.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Tải Báo Cáo CSV", csv, f"Bao_cao_{sel_year}.csv", "text/csv")

    # GIAO DIỆN CHÍNH
    st.markdown(f"## 🛡️ HỆ THỐNG QUẢN TRỊ TẬP TRUNG - {sel_year}")
    
    # KPI HÀNG ĐẦU (FILE 1)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Tổng ca hỏng", f"{len(df_final)} ca")
    kpi2.metric("Số máy hỏng", f"{df_final['MÃ_MÁY'].nunique()} máy")
    kpi3.metric("Tổng chi phí", f"{df_final['CP_THUC_TE'].sum():,.0f} đ")
    cl = df_final['CHENH_LECH'].sum()
    kpi4.metric("Chênh lệch NS", f"{cl:,.0f} đ", delta=f"{cl:,.0f}", delta_color="inverse")

    # --- HỆ THỐNG TABS PHỤC HỒI ---
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "📊 XU HƯỚNG", "💰 TÀI CHÍNH", "🤖 TRỢ LÝ AI", 
        "📁 DATA MASTER", "🩺 SỨC KHỎE", "🔮 DỰ BÁO", "🚀 KHO 2 MIỀN"
    ])

    with t1: # FIX LỖI BIỂU ĐỒ TRONG ẢNH SẾP GỬI
        st.subheader("📈 So sánh lượng máy hư qua các tháng")
        monthly_data = df_y.groupby('THÁNG').size().reset_index(name='Số ca')
        fig_trend = px.bar(monthly_data, x='THÁNG', y='Số ca', text_auto=True, color_discrete_sequence=['#007AFF'])
        fig_trend.update_xaxes(type='category') # Đảm bảo hiện đủ các tháng
        st.plotly_chart(fig_trend, use_container_width=True)

        c_p, c_t = st.columns(2)
        with c_p:
            st.plotly_chart(px.pie(df_final, names='VÙNG', title="Tỷ lệ theo Miền"), use_container_width=True)
        with c_t:
            st.plotly_chart(px.bar(df_final['MÃ_MÁY'].value_counts().head(10).reset_index(), x='count', y='MÃ_MÁY', orientation='h', title="Top 10 máy hỏng nhiều"), use_container_width=True)

    with t2:
        cost_df = df_final.groupby('LINH_KIỆN')[['CP_DU_KIEN', 'CP_THUC_TE']].sum().reset_index()
        st.plotly_chart(px.bar(cost_df, x='LINH_KIỆN', y=['CP_DU_KIEN', 'CP_THUC_TE'], barmode='group', title="Đối soát chi phí"), use_container_width=True)

    with t3:
        st.subheader("🤖 Trợ lý AI - Nhận định")
        top_m = df_final['MÃ_MÁY'].value_counts().idxmax()
        st.info(f"AI Nhận định: Máy **{top_m}** đang gặp sự cố nhiều nhất trong giai đoạn này. Cần kiểm tra điều kiện vận hành.")

    with t4: st.dataframe(df_final, use_container_width=True)

    with t5: # SỨC KHỎE
        h_db = df_hist.groupby('MÃ_MÁY').agg({'NGÀY': 'count', 'CP_THUC_TE': 'sum'}).reset_index()
        h_db.columns = ['Mã Máy', 'Tổng lần hỏng', 'Tổng chi phí']
        st.dataframe(h_db.sort_values('Tổng lần hỏng', ascending=False), use_container_width=True)

    with t6: # DỰ BÁO
        st.subheader("🔮 Dự báo & Cảnh báo sớm")
        df_s = df_hist.sort_values(['MÃ_MÁY', 'NGÀY'])
        df_s['KC'] = df_s.groupby('MÃ_MÁY')['NGÀY'].diff().dt.days
        warns = df_s[df_s['KC'] <= 60]
        if not warns.empty: st.warning(f"Cảnh báo: Có {len(warns)} máy hỏng lặp lại nhanh!")
        st.table((df_hist['LINH_KIỆN'].value_counts() / (len(df_hist['NĂM'].unique())*12)).round(1).head(5))

    with t7: # MODULE KHO MỚI
        st.header("🚀 Quản lý Kho Đà Nẵng & Miền Bắc")
        if not df_ware.empty:
            w1, w2, w3 = st.columns(3)
            w1.metric("Tổng nhận kho", len(df_ware))
            w2.metric("Đang xử lý", len(df_ware[df_ware['TRẠNG THÁI'] == "🟡 ĐANG XỬ LÝ"]))
            w3.metric("Thanh lý/Hủy", len(df_ware[df_ware['TRẠNG THÁI'] == "🔴 THANH LÝ/HỦY"]))
            
            st.plotly_chart(px.bar(df_ware.groupby(['CHI NHÁNH', 'TRẠNG THÁI']).size().reset_index(name='Số lượng'), x='CHI NHÁNH', y='Số lượng', color='TRẠNG THÁI', barmode='group'), use_container_width=True)
            st.dataframe(df_ware, use_container_width=True)
        else:
            st.error("Chưa kết nối được File Kho. Sếp hãy kiểm tra link!")

else:
    st.warning("Dữ liệu lịch sử đang trống hoặc lỗi định dạng.")
