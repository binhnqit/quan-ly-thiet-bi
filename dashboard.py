import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Thiết bị Toàn Quốc", layout="wide")

SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

# Kỹ thuật mới: Đọc dữ liệu thô không phụ thuộc vào Filter của Google Sheets
URL_RAW = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=5) # Giảm thời gian cache để sếp sửa trên Sheets là App thấy ngay
def load_data_final_v2():
    try:
        # Đọc dữ liệu từ dòng 2 (bỏ qua tiêu đề gộp ô)
        df = pd.read_csv(URL_RAW)
        
        # Ép tên cột về chuẩn để xử lý
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Tự động tìm cột Khu vực (Cột F trong hình của sếp)
        # Nếu không thấy tên, ta lấy cột thứ 6 (index 5) vì image_0333ed cho thấy nó là cột F
        col_kv = next((c for c in df.columns if "CHI NHÁNH" in c or "KHU VỰC" in c), df.columns[5])
        col_ma = next((c for c in df.columns if "MÁY" in c), df.columns[1])
        
        df = df.dropna(subset=[col_ma])
        
        # CHUẨN HÓA TOÀN DIỆN
        def final_fix(val):
            v = str(val).strip().upper()
            if any(x in v for x in ['NAM', 'MN']): return 'MIỀN NAM'
            if any(x in v for x in ['BẮC', 'MB']): return 'MIỀN BẮC'
            if any(x in v for x in ['TRUNG', 'ĐN', 'DN', 'ĐÀ NẴNG']): return 'MIỀN TRUNG / ĐÀ NẴNG'
            return 'KHÁC'

        df['Mã số máy'] = df[col_ma].astype(str).str.split('.').str[0]
        df['Vùng Miền'] = df[col_kv].apply(final_fix)
        
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

df = load_data_final_v2()

st.title("🛡️ Dashboard Quản trị Thiết bị Toàn Quốc")

if not df.empty:
    # Sidebar lọc
    all_vung = sorted(df['Vùng Miền'].unique())
    selected = st.sidebar.multiselect("📍 Chọn Miền hiển thị", all_vung, default=all_vung)
    df_filtered = df[df['Vùng Miền'].isin(selected)]

    # Chỉ số KPIs
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng ca ghi nhận", len(df_filtered))
    m2.metric("Số máy khác nhau", df_filtered['Mã số máy'].nunique())
    
    # Kiểm tra trực tiếp Miền Nam
    df_nam = df[df['Vùng Miền'] == 'MIỀN NAM']
    m3.metric("Dữ liệu Miền Nam", len(df_nam), delta="Cần kiểm tra lại Sheets" if len(df_nam) == 0 else "Đã nhận")

    st.divider()

    # Biểu đồ gộp sạch sẽ
    df_chart = df_filtered['Vùng Miền'].value_counts().reset_index()
    df_chart.columns = ['Khu vực', 'Số lượng']
    
    fig = px.bar(df_chart, x='Khu vực', y='Số lượng', color='Khu vực', text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    # CÔNG CỤ SOI DỮ LIỆU CHO SẾP
    st.subheader("🔍 Công cụ soi dữ liệu thô")
    col_check1, col_check2 = st.columns(2)
    
    with col_check1:
        st.write("Các giá trị đang có trong cột Chi Nhánh của sếp:")
        # Tìm lại tên cột gốc để hiện cho sếp xem
        col_kv_name = next((c for c in df.columns if "CHI NHÁNH" in c or "KHU VỰC" in c or "UNNAMED: 5" in c), df.columns[5])
        st.write(df[col_kv_name].unique())

    with col_check2:
        if len(df_nam) == 0:
            st.error("❌ App vẫn báo 0 ca Miền Nam. Sếp hãy thử bỏ 'Filter' trong Google Sheets rồi nhấn F5 lại nhé!")
        else:
            st.success(f"✅ Đã tìm thấy {len(df_nam)} dòng Miền Nam!")
            st.dataframe(df_nam[['Mã số máy', 'Vùng Miền']].head())

else:
    st.warning("Đang tải...")
