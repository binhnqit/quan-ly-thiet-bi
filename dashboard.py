import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hệ thống Quản lý Laptop Pro", layout="wide")

# Link ID chuẩn của sếp
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def load_data_final():
    try:
        # BƯỚC NGOẶT: header=1 nghĩa là bỏ qua dòng 0 (dòng tiêu đề to) 
        # và lấy dòng 1 (dòng Masomay) làm tiêu đề chính.
        df = pd.read_csv(URL, header=1)
        
        # Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        # Kiểm tra cột Masomay
        if "Masomay" in df.columns:
            df = df.dropna(subset=["Masomay"])
            # Xử lý mã máy
            df["Masomay"] = df["Masomay"].astype(str).str.split('.').str[0]
            return df
        else:
            # Nếu vẫn không thấy, in ra để sếp kiểm soát
            st.warning(f"Dòng tiêu đề đang nhận được là: {list(df.columns)}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {e}")
        return pd.DataFrame()

df = load_data_final()

st.title("🛡️ Dashboard Quản trị Thiết bị Pro")

if not df.empty:
    st.success("✅ KẾT NỐI THÀNH CÔNG RỒI SẾP ƠI!")
    
    # Hiển thị số liệu
    c1, c2 = st.columns(2)
    c1.metric("Tổng ca lỗi", len(df))
    if "Chi Nhánh" in df.columns:
        c2.metric("Chi nhánh lỗi nhiều nhất", df["Chi Nhánh"].value_counts().idxmax())

    # Bảng dữ liệu
    st.subheader("📋 Nhật ký chi tiết")
    st.dataframe(df, use_container_width=True)
    
    # Biểu đồ
    if "Chi Nhánh" in df.columns:
        fig = px.bar(df["Chi Nhánh"].value_counts().reset_index(), x='index', y='Chi Nhánh', title="Lỗi theo Chi nhánh")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 Mẹo: Sếp hãy kiểm tra xem hàng chứa chữ 'Masomay' có đúng là hàng thứ 2 trong file không nhé.")
