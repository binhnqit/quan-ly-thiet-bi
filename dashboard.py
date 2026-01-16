import streamlit as st
import pandas as pd

# Link ID gốc
SHEET_ID = "16eiLNG46MCmS5GeETnotXW5GyNtvKNYBh_7Zk7IJRfA"

# Kỹ thuật load Miền Nam nếu nó nằm ở Sheet khác (sếp thay tên Sheet cho đúng nhé)
@st.cache_data(ttl=60)
def load_all_regions():
    try:
        # Link đọc trực tiếp Tab Miền Bắc (Sheet 1)
        url_bac = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Laptop%20Miền%20Bắc"
        df_bac = pd.read_csv(url_bac, header=1)
        
        # Link đọc trực tiếp Tab Miền Nam (Sếp kiểm tra tên Tab trong Sheets nhé)
        # Nếu Tab tên là "Miền Nam", dùng link này:
        url_nam = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Miền%20Nam"
        try:
            df_nam = pd.read_csv(url_nam, header=1)
            # Gộp 2 miền lại
            df_final = pd.concat([df_bac, df_nam], ignore_index=True)
            st.sidebar.success("💡 Đã kết nối dữ liệu Liên Miền (Bắc - Nam)")
        except:
            df_final = df_bac
            st.sidebar.warning("⚠️ Không tìm thấy Tab 'Miền Nam', đang chỉ hiện Miền Bắc.")
            
        return df_final
    except Exception as e:
        return pd.DataFrame()
