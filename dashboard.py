import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản trị Pro", layout="wide")

# Link gốc Google Sheets của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
# Sử dụng export CSV truyền thống nhưng tăng giới hạn dòng
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=5)
def load_data_final_v3():
    try:
        # Đọc dữ liệu thô
        df = pd.read_csv(URL, header=None) # Đọc không header để soi lỗi
        
        # 1. Tìm dòng chứa tiêu đề (thường là dòng 1 hoặc 2)
        # Chúng ta sẽ quét 5 dòng đầu để tìm cột "Chi Nhánh" hoặc "Masomay"
        header_row = 0
        for i in range(5):
            row_str = " ".join(df.iloc[i].astype(str).upper())
            if "CHI NHÁNH" in row_str or "MASOMAY" in row_str:
                header_row = i
                break
        
        # Đọc lại với đúng header
        df = pd.read_csv(URL, header=header_row)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # 2. Xác định cột quan trọng bằng vị trí (Cột B là Máy, Cột F là Chi Nhánh)
        # Điều này giúp tránh lỗi sếp đổi tên tiêu đề
        col_ma = df.columns[1] if len(df.columns) > 1 else None
        col_kv = df.columns[5] if len(df.columns) > 5 else None
        
        if col_ma:
            df = df.dropna(subset=[col_ma])
            
            # CHUẨN HÓA DỮ LIỆU MIỀN (Dùng cho cả MN, DN, Bắc, Nam...)
            def clean_region(val):
                v = str(val).strip().upper()
                if "NAM" in v or v == "MN": return "MIỀN NAM"
                if "BẮC" in name or v == "MB": return "MIỀN BẮC"
                if any(x in v for x in ["TRUNG", "ĐN", "DN", "ĐÀ NẴNG"]): return "MIỀN TRUNG / ĐÀ NẴNG"
                return "KHÁC/CHƯA NHẬP"

            df['Vùng Miền'] = df[col_kv].apply(clean_region) if col_kv else "N/A"
            df['Mã số máy'] = df[col_ma].astype(str).str.split('.').str[0]
            
            return df, col_kv
        return pd.DataFrame(), None
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return pd.DataFrame(), None

df, col_name_raw = load_data_final_v3()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    # Sidebar lọc
    vung_mien_list = sorted(df['Vùng Miền'].unique())
    selected = st.sidebar.multiselect("📍 Lọc Vùng Miền", vung_mien_list, default=vung_mien_list)
    df_filtered = df[df['Vùng Miền'].isin(selected)]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ca sửa chữa", len(df_filtered))
    c2.metric("Số lượng máy hỏng", df_filtered['Mã số máy'].nunique())
    
    # Kiểm đếm Miền Nam
    num_nam = len(df[df['Vùng Miền'] == 'MIỀN NAM'])
    c3.metric("Dữ liệu Miền Nam", num_nam, delta="Đã nhận diện" if num_nam > 0 else "Chưa thấy")

    st.divider()

    # Biểu đồ
    if not df_filtered.empty:
        chart_data = df_filtered['Vùng Miền'].value_counts().reset_index()
        chart_data.columns = ['Khu vực', 'Số lượng']
        fig = px.bar(chart_data, x='Khu vực', y='Số lượng', color='Khu vực', text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    # 🔍 PHẦN QUAN TRỌNG: SOI LỖI CHO SẾP
    with st.expander("🛠️ TRÌNH KIỂM TRA DỮ LIỆU (Dành cho sếp)"):
        st.write(f"Tên cột Khu vực App tìm thấy: **{col_name_raw}**")
        st.write("Các giá trị gốc trong file của sếp (10 dòng đầu):")
        st.write(df[col_name_raw].unique())
        
        if num_nam == 0:
            st.error("❗ CẢNH BÁO: App không thấy chữ 'NAM' hoặc 'MN' nào trong cột này.")
            st.write("Sếp hãy kiểm tra xem trong file Sheets, cột Chi Nhánh (Cột F) có thực sự đã nhập dữ liệu cho Miền Nam chưa, hay mới chỉ có màu xanh mà chưa có chữ?")

else:
    st.warning("Đang kết nối lại với Google Sheets... Sếp kiểm tra Link Share nhé!")
