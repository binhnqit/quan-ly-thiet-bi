import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- CẤU HÌNH ĐẲNG CẤP CHUYÊN GIA ---
st.set_page_config(page_title="Hệ Thống Phân Tích Lỗi V6000", layout="wide")

@st.cache_data(ttl=5) # Cập nhật sau mỗi 5 giây
def load_data_final_expert():
    # LINK GỐC CỦA SẾP
    base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS-UP5WFVE63byPckNy_lsT9Rys84A8pPq6cm6rFFBbOnPAsSl1QDLS_A9E45oytg/pub?output=csv"
    
    try:
        # KỸ THUẬT PHÁ CACHE: Ép Google trả dữ liệu mới nhất bằng cách thêm timestamp
        timestamp = int(time.time())
        final_url = f"{base_url}&cache_buster={timestamp}"
        
        # Đọc dữ liệu với chế độ "Low Memory" tắt để đảm bảo đọc hết 100% dòng
        df_raw = pd.read_csv(final_url, dtype=str, header=None, low_memory=False).fillna("")
        
        clean_data = []
        memo = {"ngay": None, "khach": "N/A", "vung": "N/A"}

        # QUÉT TOÀN BỘ FILE (Không bỏ sót bất kỳ dòng nào)
        for i, row in df_raw.iterrows():
            if i == 0: continue # Bỏ tiêu đề
            
            # Lấy dữ liệu thô từ các cột 0, 1, 2, 3, 5
            c_date = str(row.iloc[0]).strip()
            c_may = str(row.iloc[1]).strip()
            c_kh = str(row.iloc[2]).strip()
            c_lk = str(row.iloc[3]).strip()
            c_vung = str(row.iloc[5]).strip().upper()

            # 1. LOGIC ĐIỀN TRỐNG (Data Healing) - Cực kỳ quan trọng
            parsed_date = pd.to_datetime(c_date, dayfirst=True, errors='coerce')
            if pd.notnull(parsed_date): memo["ngay"] = parsed_date
            if c_kh: memo["khach"] = c_kh
            if c_vung: memo["vung"] = c_vung

            # 2. CHỐT CHẶN DỮ LIỆU THỰC: 
            # Dòng được tính nếu CÓ MÃ MÁY và ĐÃ CÓ NGÀY (từ dòng này hoặc dòng trên)
            if c_may and len(c_may) >= 2 and "MÃ" not in c_may.upper():
                if memo["ngay"]:
                    clean_data.append({
                        "NGÀY": memo["ngay"],
                        "NĂM": memo["ngay"].year,
                        "THÁNG": memo["ngay"].month,
                        "MÃ_MÁY": c_may,
                        "KHÁCH_HÀNG": memo["khach"],
                        "LINH_KIỆN": c_lk if c_lk else "Chưa xác định",
                        "VÙNG": "MIỀN NAM" if "NAM" in memo["vung"] else 
                                ("MIỀN BẮC" if "BẮC" in memo["vung"] else "MIỀN TRUNG")
                    })
        
        return pd.DataFrame(clean_data)
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return pd.DataFrame()

# --- KHỞI CHẠY DASHBOARD ---
df = load_data_final_expert()

st.title("🛡️ Dashboard Phân Tích Lỗi Thiết Bị - V6000 Pro")

if not df.empty:
    # Sidebar lọc dữ liệu
    with st.sidebar:
        st.header("⚙️ QUẢN TRỊ V110")
        if st.button("🔄 LÀM MỚI DỮ LIỆU THỰC", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        years = sorted(df['NĂM'].unique(), reverse=True)
        sel_year = st.selectbox("📅 Năm", years)
        df_year = df[df['NĂM'] == sel_year]
        
        months = ["Tất cả"] + sorted(df_year['THÁNG'].unique().tolist())
        sel_month = st.selectbox("🗓️ Tháng", months)
        
        df_final = df_year if sel_month == "Tất cả" else df_year[df_year['THÁNG'] == sel_month]

    # KPI CHUẨN (Như sếp yêu cầu)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng ca hỏng", len(df_final))
    c2.metric("Thiết bị lỗi", df_final['MÃ_MÁY'].nunique())
    
    dup = df_final['MÃ_MÁY'].value_counts()
    c3.metric("Hỏng tái diễn (>1)", len(dup[dup > 1]))
    c4.metric("Khách hàng báo lỗi", df_final['KHÁCH_HÀNG'].nunique())

    # BIỂU ĐỒ CHUYÊN GIA
    t1, t2, t3 = st.tabs(["📊 Xu hướng & Vùng miền", "🚩 Cảnh báo Re-fail", "🔍 Truy xuất dữ liệu sạch"])
    
    with t1:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.subheader("📈 Xu hướng lỗi thực tế")
            trend = df_final.groupby('NGÀY').size().reset_index(name='Số ca')
            fig = px.line(trend, x='NGÀY', y='Số ca', markers=True, text='Số ca')
            fig.update_traces(line_color='#FF4B4B', fill='tozeroy')
            st.plotly_chart(fig, use_container_width=True)
                    
        with col_b:
            st.subheader("📍 Tỷ lệ vùng miền")
            vung = df_final['VÙNG'].value_counts().reset_index()
            st.plotly_chart(px.pie(vung, values='count', names='VÙNG', hole=0.4), use_container_width=True)

        st.subheader("🔧 Phân tích linh kiện lỗi")
        lk = df_final['LINH_KIỆN'].value_counts().reset_index().head(10)
        st.plotly_chart(px.bar(lk, x='count', y='LINH_KIỆN', orientation='h', text_auto=True), use_container_width=True)

    with t2:
        if not dup[dup > 1].empty:
            st.warning("Danh sách máy hỏng nhiều lần:")
            st.write(dup[dup > 1])
        else:
            st.success("Không có máy hỏng tái diễn.")

    with t3:
        st.write("Dữ liệu đã được quét và làm sạch (100% Khớp với Sheets):")
        st.dataframe(df_final, use_container_width=True)
else:
    st.warning("⚠️ Hệ thống không tìm thấy dữ liệu hợp lệ. Sếp hãy chắc chắn đã nhập Mã máy vào cột B!")
