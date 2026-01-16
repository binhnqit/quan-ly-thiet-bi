import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Laptop Pro", layout="wide")

PUBLISHED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRuNH37yVPVZsAOyyJ4Eqvc0Hsd5XvucmKvw1XyZwhkeV6YVuxhZ14ACHxrtQf-KD-fP0yWlbgpdat-/pub?gid=675485241&single=true&output=csv"

@st.cache_data(ttl=60)
def load_full_feature_data():
    try:
        df = pd.read_csv(PUBLISHED_URL, on_bad_lines='skip')
        df.columns = [f"COL_{i}" for i in range(len(df.columns))]
        
        # Tiền xử lý dữ liệu chuẩn
        def detect_region(row):
            val_col3 = str(row['COL_3']).upper()
            full_text = " ".join(row.astype(str)).upper()
            target = val_col3 if "MIỀN" in val_col3 else full_text
            if any(x in target for x in ["NAM", "MN"]): return "Miền Nam"
            if any(x in target for x in ["BẮC", "MB"]): return "Miền Bắc"
            if any(x in target for x in ["TRUNG", "ĐN", "DN"]): return "Miền Trung"
            return "Khác/Chưa nhập"

        df['VÙNG_MIỀN'] = df.apply(detect_region, axis=1)
        df['MÃ_MÁY'] = df['COL_1'].astype(str).str.split('.').str[0]
        df['LINH_KIỆN'] = df['COL_4'].fillna("Không xác định")
        df['NGAY_FIX'] = pd.to_datetime(df['COL_6'], errors='coerce', dayfirst=True)
        
        # Loại bỏ rác dữ liệu
        df = df[df['MÃ_MÁY'] != 'nan']
        df = df[~df['MÃ_MÁY'].str.contains("STT|MÃ|THEO", na=False)]
        return df
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

df = load_full_feature_data()

# --- SIDEBAR: CÔNG CỤ TÌM KIẾM & LỌC ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2504/2504814.png", width=100)
    st.header("🔍 Trung tâm Điều khiển")
    
    search_query = st.text_input("Tìm theo Mã máy hoặc Linh kiện", placeholder="Ví dụ: 2498 hoặc Phím...")
    
    selected_regions = st.multiselect("Lọc theo Vùng", 
                                      ["Miền Bắc", "Miền Trung", "Miền Nam", "Khác/Chưa nhập"], 
                                      default=["Miền Bắc", "Miền Trung", "Miền Nam"])
    
    st.divider()
    st.info(f"Dòng cuối cùng: {df['COL_0'].iloc[-1] if not df.empty else 0}")

# Ứng dụng bộ lọc
mask = df['VÙNG_MIỀN'].isin(selected_regions)
if search_query:
    mask = mask & (df['MÃ_MÁY'].str.contains(search_query, case=False) | 
                   df['LINH_KIỆN'].str.contains(search_query, case=False))
df_filtered = df[mask]

# --- GIAO DIỆN CHÍNH ---
st.title("🛡️ Dashboard Quản trị Thiết bị Laptop Pro")

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Tổng lượt lỗi", f"{len(df_filtered):,}")
k2.metric("Số máy đang quản lý", f"{df_filtered['MÃ_MÁY'].nunique():,}")
repeat_count = (df_filtered['MÃ_MÁY'].value_counts() > 1).sum()
k3.metric("Máy lỗi lặp lại (>1 lần)", f"{repeat_count:,}", delta_color="inverse")
k4.metric("Dữ liệu Miền Nam", f"{len(df_filtered[df_filtered['VÙNG_MIỀN']=='Miền Nam']):,}")

st.divider()

# BIỂU ĐỒ PHÂN TÍCH CHUYÊN SÂU
c_left, c_right = st.columns(2)

with c_left:
    st.subheader("📊 Phân bổ lỗi theo Vùng")
    vung_data = df_filtered['VÙNG_MIỀN'].value_counts().reset_index()
    fig_vung = px.bar(vung_data, x='VÙNG_MIỀN', y='count', color='VÙNG_MIỀN', text_auto=True,
                     color_discrete_map={"Miền Nam": "#28a745", "Miền Bắc": "#007bff", "Miền Trung": "#ffc107"})
    st.plotly_chart(fig_vung, use_container_width=True)

with c_right:
    st.subheader("🛠️ Top 10 Linh kiện hay hỏng")
    lk_data = df_filtered['LINH_KIỆN'].value_counts().head(10).reset_index()
    fig_lk = px.pie(lk_data, values='count', names='LINH_KIỆN', hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_lk, use_container_width=True)

st.divider()

# THỐNG KÊ MÁY "BỆNH NẶNG"
st.subheader("🚨 Top 10 Máy hỏng nhiều lần nhất (Cần thanh lý/Kiểm tra)")
top_bad_machines = df_filtered['MÃ_MÁY'].value_counts().head(10).reset_index()
top_bad_machines.columns = ['Mã Máy', 'Số lần ghi nhận lỗi']
st.table(top_bad_machines)

# DANH SÁCH CHI TIẾT
st.subheader("📋 Danh sách dữ liệu chi tiết")
st.dataframe(df_filtered[['MÃ_MÁY', 'VÙNG_MIỀN', 'LINH_KIỆN', 'COL_6']].tail(100), use_container_width=True)
