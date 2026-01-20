import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- 1. GIỮ NGUYÊN CẤU HÌNH & DATA FILE GỐC (V15.2) ---
st.set_page_config(page_title="Hệ Thống Quản Trị V16.2", layout="wide")

@st.cache_data(ttl=2)
def load_data_goc():
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

# --- 2. MODULE TAB MỚI: ĐỌC FILE KHO 2 MIỀN (CHỈ THÊM, KHÔNG SỬA CODE TRÊN) ---
@st.cache_data(ttl=2)
def load_data_kho_moi():
    # Sử dụng link xuất CSV trực tiếp để tránh lỗi kết nối
    sheet_id = "1GaWsUJutV4wixR3RUBZSTIMrgaD8fOIi"
    gid_dn = "602348620"
    gid_mb = "1626219342"
    
    def get_df(gid):
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        try:
            df = pd.read_csv(url).fillna("")
            df.columns = [c.strip().upper() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df_dn = get_df(gid_dn)
    df_mb = get_df(gid_mb)
    
    combined = []
    for branch, df_sub in [("ĐÀ NẴNG", df_dn), ("MIỀN BẮC", df_mb)]:
        if not df_sub.empty:
            for _, row in df_sub.iterrows():
                ma = str(row.get('MÃ SỐ MÁY', '')).strip()
                if not ma: continue
                d_nhan = pd.to_datetime(row.get('NGÀY NHẬN', ''), dayfirst=True, errors='coerce')
                d_tra = pd.to_datetime(row.get('NGÀY TRẢ', ''), dayfirst=True, errors='coerce')
                sua_nb = str(row.get('SỬA NỘI BỘ', '')).upper()
                
                status = "🟡 ĐANG XỬ LÝ"
                if pd.notnull(d_tra) or "OK" in str(row.get('GIAO LẠI ĐN', '')).upper():
                    status = "🟢 ĐÃ TRẢ/XONG"
                if "THANH LÝ" in sua_nb or str(row.get('HƯ KHÔNG SỬA ĐƯỢC', '')) != "":
                    status = "🔴 THANH LÝ"
                
                combined.append({
                    "CHI NHÁNH": branch, "MÃ MÁY": ma, "NGÀY NHẬN": d_nhan,
                    "TRẠNG THÁI": status, "LOẠI MÁY": row.get('LOẠI MÁY', ''),
                    "KIỂM TRA": row.get('KIỂM TRA THỰC TẾ', '')
                })
    return pd.DataFrame(combined)

# --- 3. KHỞI CHẠY HỆ THỐNG ---
df = load_data_goc()
df_kho = load_data_kho_moi()

if not df.empty:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3208/3208726.png", width=80)
        st.title("EXECUTIVE HUB")
        if st.button('🔄 ĐỒNG BỘ HỆ THỐNG'):
            st.cache_data.clear()
            st.rerun()
        
        sel_year = st.selectbox("📅 Năm báo cáo", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.multiselect("🗓️ Lọc Tháng", sorted(df_y['THÁNG'].unique()), default=sorted(df_y['THÁNG'].unique()))
        df_final = df_y[df_y['THÁNG'].isin(sel_month)]

    st.markdown(f"## 🛡️ QUẢN TRỊ THIẾT BỊ V16.2")
    
    # --- 4. TABS: GIỮ NGUYÊN 6 TAB CŨ, CHỈ THÊM TAB 7 ---
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "📊 PHÂN TÍCH XU HƯỚNG", "💰 TÀI CHÍNH CHI TIẾT", "🤖 TRỢ LÝ AI", 
        "📁 DỮ LIỆU SẠCH", "🩺 SỨC KHỎE & THANH LÝ", "🔮 DỰ BÁO & CẢNH BÁO", "🚀 KHO 2 CHI NHÁNH"
    ])

    with t1: # KHÔI PHỤC BIỂU ĐỒ XU HƯỚNG CŨ
        st.subheader("📈 So sánh lượng máy hư qua các tháng")
        monthly_trend = df_y.groupby('THÁNG').size().reset_index(name='Số ca')
        fig_trend = px.bar(monthly_trend, x='THÁNG', y='Số ca', text_auto=True, color_discrete_sequence=['#007AFF'])
        fig_trend.update_xaxes(type='category')
        st.plotly_chart(fig_trend, use_container_width=True)

    with t2: # KHÔI PHỤC TÀI CHÍNH CŨ
        cost_data = df_final.groupby('LINH_KIỆN')[['CP_DU_KIEN', 'CP_THUC_TE']].sum().reset_index()
        st.plotly_chart(px.bar(cost_data, x='LINH_KIỆN', y=['CP_DU_KIEN', 'CP_THUC_TE'], barmode='group'), use_container_width=True)

    with t3: # KHÔI PHỤC AI CŨ
        st.info(f"AI: Máy {df_final['MÃ_MÁY'].value_counts().idxmax()} cần chú ý đặc biệt.")

    with t4: st.dataframe(df_final, use_container_width=True)

    with t5: # KHÔI PHỤC SỨC KHỎE CŨ
        h_db = df.groupby('MÃ_MÁY').agg({'NGÀY': 'count', 'CP_THUC_TE': 'sum'}).reset_index()
        st.dataframe(h_db.sort_values('NGÀY', ascending=False), use_container_width=True)

    with t6: # KHÔI PHỤC DỰ BÁO CŨ (FIX LỖI MẤT BIỂU ĐỒ)
        st.subheader("🔮 Dự báo & Cảnh báo sớm")
        df_sorted = df.sort_values(['MÃ_MÁY', 'NGÀY'])
        df_sorted['KHOANG_CACH'] = df_sorted.groupby('MÃ_MÁY')['NGÀY'].diff().dt.days
        warnings = df_sorted[df_sorted['KHOANG_CACH'] <= 60]
        if not warnings.empty:
            st.warning(f"Cảnh báo: Có {len(warnings)} máy hỏng lặp lại nhanh!")
            st.dataframe(warnings[['MÃ_MÁY', 'NGÀY', 'KHOANG_CACH']], use_container_width=True)

    with t7: # TAB MỚI: KHO 2 CHI NHÁNH
        st.header("🚀 Kho Đà Nẵng & Miền Bắc")
        if not df_kho.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng nhận", len(df_kho))
            c2.metric("Đang xử lý", len(df_kho[df_kho['TRẠNG THÁI']=="🟡 ĐANG XỬ LÝ"]))
            c3.metric("Thanh lý", len(df_kho[df_kho['TRẠNG THÁI']=="🔴 THANH LÝ"]))
            
            st.plotly_chart(px.bar(df_kho.groupby(['CHI NHÁNH', 'TRẠNG THÁI']).size().reset_index(name='Số lượng'), x='CHI NHÁNH', y='Số lượng', color='TRẠNG THÁI', barmode='group'), use_container_width=True)
            st.dataframe(df_kho, use_container_width=True)
        else:
            st.error("Lỗi kết nối File Kho. Sếp hãy kiểm tra lại quyền 'Chia sẻ' (Anyone with link) của file Google Sheets mới.")
