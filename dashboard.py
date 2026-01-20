import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Quản Trị Nhất Thể V16", layout="wide")

# ==========================================
# MODULE 1: DỮ LIỆU LỊCH SỬ (FILE CŨ)
# ==========================================
@st.cache_data(ttl=2)
def load_data_old_file():
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

# ==========================================
# MODULE 2: QUẢN LÝ KHO 2 MIỀN (FILE MỚI)
# ==========================================
@st.cache_data(ttl=2)
def load_dual_branch_data():
    sheet_id = "1GaWsUJutV4wixR3RUBZSTIMrgaD8fOIi"
    # GID cho Đà Nẵng (602348620) và Miền Bắc (1626219342)
    urls = {
        "ĐÀ NẴNG": f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=602348620",
        "MIỀN BẮC": f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1626219342"
    }
    all_data = []
    for branch, url in urls.items():
        try:
            # Đọc từ dòng 1 (Tiêu đề cột)
            df_temp = pd.read_csv(url, skiprows=0).fillna("")
            df_temp.columns = [c.strip().upper() for c in df_temp.columns]
            for _, row in df_temp.iterrows():
                ma_may = str(row.get('MÃ SỐ MÁY', '')).strip()
                if not ma_may or len(ma_may) < 2: continue
                
                d_nhan = pd.to_datetime(row.get('NGÀY NHẬN', ''), dayfirst=True, errors='coerce')
                d_tra = pd.to_datetime(row.get('NGÀY TRẢ', ''), dayfirst=True, errors='coerce')
                sua_nb = str(row.get('SỬA NỘI BỘ', '')).upper()
                hu_ko_sua = str(row.get('HƯ KHÔNG SỬA ĐƯỢC', '')).strip()

                # Logic phân loại trạng thái chuyên gia
                status = "🟢 ĐÃ TRẢ/XONG" if pd.notnull(d_tra) or "OK" in str(row.get('GIAO LẠI ĐN', '')).upper() else "🟡 ĐANG XỬ LÝ"
                if "THANH LÝ" in sua_nb or hu_ko_sua != "": status = "🔴 THANH LÝ/HỦY"

                all_data.append({
                    "CHI NHÁNH": branch, "MÃ MÁY": ma_may, "NGÀY NHẬN": d_nhan,
                    "NGÀY TRẢ": d_tra, "TRẠNG THÁI": status, "LOẠI MÁY": row.get('LOẠI MÁY', ''),
                    "SỬA NGOÀI": row.get('SỬA BÊN NGOÀI', ''), "KIỂM TRA": row.get('KIỂM TRA THỰC TẾ', '')
                })
        except: continue
    return pd.DataFrame(all_data)

# --- CHẠY HỆ THỐNG ---
df_old = load_data_old_file()
df_new = load_dual_branch_data()

# GIAO DIỆN EXECUTIVE
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208726.png", width=80)
    st.title("EXECUTIVE HUB V16")
    if st.button('🔄 ĐỒNG BỘ TOÀN HỆ THỐNG'):
        st.cache_data.clear()
        st.rerun()

# PHÂN CHIA TABS NHẤT THỂ
t1, t2, t3, t4, t5, t6, t7 = st.tabs([
    "📊 XU HƯỚNG", "💰 TÀI CHÍNH", "🤖 AI AI", 
    "📁 DATA MASTER", "🩺 SỨC KHỎE", "🔮 DỰ BÁO", "🚀 KHO 2 CHI NHÁNH"
])

# [Tab 1-6 giữ nguyên logic từ V15.2 của sếp - Không thay đổi code cũ]
with t1:
    if not df_old.empty:
        st.subheader("Phân tích từ File Lịch sử cũ")
        st.plotly_chart(px.bar(df_old.groupby('THÁNG').size().reset_index(), x='THÁNG', y=0, text_auto=True, title="Số ca hỏng theo tháng"), use_container_width=True)

# TAB 7: ĐIỂM NHẤN MỚI
with t7:
    st.header("🚀 Quản Lý Luồng Máy Đà Nẵng & Miền Bắc")
    if not df_new.empty:
        # KPI của Case mới
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Tổng Nhận (Kho)", len(df_new))
        k2.metric("Đang xử lý", len(df_new[df_new['TRẠNG THÁI'] == "🟡 ĐANG XỬ LÝ"]))
        k3.metric("Thanh lý/Hủy", len(df_new[df_new['TRẠNG THÁI'] == "🔴 THANH LÝ/HỦY"]))
        k4.metric("Đã hoàn thành", len(df_new[df_new['TRẠNG THÁI'] == "🟢 ĐÃ TRẢ/XONG"]))

        # Biểu đồ so sánh 2 miền
        st.subheader("So sánh hiệu suất 2 chi nhánh")
        fig_br = px.bar(df_new.groupby(['CHI NHÁNH', 'TRẠNG THÁI']).size().reset_index(name='Số lượng'), 
                        x='CHI NHÁNH', y='Số lượng', color='TRẠNG THÁI', barmode='group')
        st.plotly_chart(fig_br, use_container_width=True)
        

        st.subheader("Danh sách chi tiết kho hiện tại")
        st.dataframe(df_new, use_container_width=True)
    else:
        st.warning("Đang kết nối tới File mới, vui lòng chờ...")

# Các tab khác sếp cứ giữ nguyên logic hiển thị từ bản V15.2
