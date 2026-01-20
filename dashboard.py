import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- GIỮ NGUYÊN CẤU HÌNH V15.2 ---
st.set_page_config(page_title="Hệ Thống Quản Trị V16.3", layout="wide")

@st.cache_data(ttl=2)
def load_data_v15_2():
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

# --- CHỈ THÊM: MODULE ĐỌC KHO MỚI (KHÔNG CHẠM CODE CŨ) ---
@st.cache_data(ttl=2)
def load_kho_moi():
    try:
        # Link Google Sheet mới sếp gửi (Dạng Export CSV)
        sheet_url = "https://docs.google.com/spreadsheets/d/1GaWsUJutV4wixR3RUBZSTIMrgaD8fOIi/export?format=csv&gid=602348620"
        df_k = pd.read_csv(sheet_url).fillna("")
        df_k.columns = [c.strip().upper() for c in df_k.columns]
        
        processed = []
        for _, row in df_k.iterrows():
            ma = str(row.get('MÃ SỐ MÁY', '')).strip()
            if not ma: continue
            
            d_nhan = pd.to_datetime(row.get('NGÀY NHẬN', ''), dayfirst=True, errors='coerce')
            d_tra = pd.to_datetime(row.get('NGÀY TRẢ', ''), dayfirst=True, errors='coerce')
            sua_nb = str(row.get('SỬA NỘI BỘ', '')).upper()
            
            # Logic trạng thái
            status = "🟡 ĐANG XỬ LÝ"
            if pd.notnull(d_tra) or "OK" in str(row.get('GIAO LẠI ĐN', '')).upper():
                status = "🟢 ĐÃ TRẢ"
            if "THANH LÝ" in sua_nb or str(row.get('HƯ KHÔNG SỬA ĐƯỢC', '')) != "":
                status = "🔴 THANH LÝ"
                
            processed.append({
                "MÃ MÁY": ma, "KHU VỰC": row.get('KHU VỰC', 'ĐN'),
                "NGÀY NHẬN": d_nhan, "NGÀY TRẢ": d_tra,
                "TRẠNG THÁI": status, "LOẠI MÁY": row.get('LOẠI MÁY', '')
            })
        return pd.DataFrame(processed)
    except: return pd.DataFrame()

# --- VẬN HÀNH ---
df = load_data_v15_2()
df_kho = load_kho_moi()

if not df.empty:
    with st.sidebar:
        st.title("EXECUTIVE HUB")
        if st.button('🔄 ĐỒNG BỘ HỆ THỐNG'):
            st.cache_data.clear()
            st.rerun()
        sel_year = st.selectbox("📅 Năm báo cáo", sorted(df['NĂM'].unique(), reverse=True))
        df_y = df[df['NĂM'] == sel_year]
        sel_month = st.multiselect("🗓️ Lọc Tháng", sorted(df_y['THÁNG'].unique()), default=sorted(df_y['THÁNG'].unique()))
        df_final = df_y[df_y['THÁNG'].isin(sel_month)]

    st.markdown(f"## 🛡️ QUẢN TRỊ THIẾT BỊ V16.3")
    
    # --- CẤU TRÚC TAB V15.2 NGUYÊN BẢN ---
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "📊 PHÂN TÍCH XU HƯỚNG", "💰 TÀI CHÍNH CHI TIẾT", "🤖 TRỢ LÝ AI", 
        "📁 DỮ LIỆU SẠCH", "🩺 SỨC KHỎE & THANH LÝ", "🔮 DỰ BÁO & CẢNH BÁO", "🚀 KHO CHI NHÁNH MỚI"
    ])

    with t1: # KHÔI PHỤC BIỂU ĐỒ THÁNG (FIX LỖI ẢNH 1)
        st.subheader("📈 So sánh lượng máy hư qua các tháng")
        m_data = df_y.groupby('THÁNG').size().reset_index(name='Số ca')
        fig = px.bar(m_data, x='THÁNG', y='Số ca', text_auto=True, color_discrete_sequence=['#007AFF'])
        fig.update_xaxes(type='category', title="Tháng") # Đảm bảo hiện 1, 2, 3...
        st.plotly_chart(fig, use_container_width=True)

    with t2: # TÀI CHÍNH V15.2
        c_data = df_final.groupby('LINH_KIỆN')[['CP_DU_KIEN', 'CP_THUC_TE']].sum().reset_index()
        st.plotly_chart(px.bar(c_data, x='LINH_KIỆN', y=['CP_DU_KIEN', 'CP_THUC_TE'], barmode='group'), use_container_width=True)

    with t3: # AI V15.2
        st.info(f"AI: Máy {df_final['MÃ_MÁY'].value_counts().idxmax()} đang hỏng nhiều nhất.")

    with t4: st.dataframe(df_final, use_container_width=True)

    with t5: # SỨC KHỎE V15.2
        st.dataframe(df.groupby('MÃ_MÁY').size().reset_index(name='Số lần hỏng').sort_values('Số lần hỏng', ascending=False), use_container_width=True)

    with t6: # DỰ BÁO V15.2
        st.subheader("🔮 Dự báo & Cảnh báo sớm")
        # Logic cảnh báo 60 ngày nguyên bản
        df_s = df.sort_values(['MÃ_MÁY', 'NGÀY'])
        df_s['KC'] = df_s.groupby('MÃ_MÁY')['NGÀY'].diff().dt.days
        warns = df_s[df_s['KC'] <= 60]
        if not warns.empty:
            st.warning(f"Cảnh báo: Có {len(warns)} máy hỏng lặp lại nhanh!")

    with t7: # TAB BỔ SUNG (CASE MỚI)
        st.header("🚀 Quản lý Kho Đà Nẵng")
        if not df_kho.empty:
            col1, col2 = st.columns(2)
            col1.metric("Tổng nhận", len(df_kho))
            col2.metric("Thanh lý/Hư", len(df_kho[df_kho['TRẠNG THÁI'] == "🔴 THANH LÝ"]))
            st.dataframe(df_kho, use_container_width=True)
        else:
            st.error("Lỗi: Chưa đọc được File Kho. Sếp hãy kiểm tra quyền chia sẻ file mới!")
