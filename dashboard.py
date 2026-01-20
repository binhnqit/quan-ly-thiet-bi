# --- Thêm đoạn này vào trong Tab 4 (AI ĐỀ XUẤT) của hàm main() ---

st.divider()
st.markdown("#### 🔮 Module 3: Dự báo bảo trì chủ động (Predictive Maintenance)")

# 1. Tính toán ngày cách biệt từ lần sửa cuối
df_predict = df_f.sort_values(['MÃ_MÁY', 'NGÀY'])
df_predict['Ngay_Truoc'] = df_predict.groupby('MÃ_MÁY')['NGÀY'].shift(1)
df_predict['Khoang_Cach'] = (df_predict['NGÀY'] - df_predict['Ngay_Truoc']).dt.days

# Tính khoảng cách trung bình giữa các lần hỏng của toàn hệ thống
avg_gap = df_predict['Khoang_Cach'].mean() if not df_predict['Khoang_Cach'].dropna().empty else 90

col_p1, col_p2 = st.columns([1, 2])
with col_p1:
    st.metric("NHỊP HỎNG TB (Ngày)", f"{avg_gap:.0f} ngày")
    st.write(f"👉 AI nhận định: Cứ sau khoảng **{avg_gap:.0f} ngày**, thiết bị có xu hướng phát sinh lỗi mới.")

with col_p2:
    # Tìm các máy đã quá "nhịp hỏng" kể từ lần sửa cuối (giả sử hôm nay là ngày cuối cùng trong data)
    last_date = df_f['NGÀY'].max()
    latest_repair = df_f.groupby('MÃ_MÁY')['NGÀY'].max().reset_index()
    latest_repair['Days_Since'] = (last_date - latest_repair['NGÀY']).dt.days
    
    # Cảnh báo các máy đang nằm trong "Vùng nguy hiểm" (gần đến nhịp hỏng tiếp theo)
    warning_machines = latest_repair[(latest_repair['Days_Since'] > avg_gap * 0.8) & (latest_repair['Days_Since'] < avg_gap * 1.2)]
    
    if not warning_machines.empty:
        st.warning(f"Phát hiện {len(warning_machines)} máy đang chạm ngưỡng hỏng hóc dự báo.")
        st.write("Sếp nên yêu cầu kỹ thuật kiểm tra tổng thể các máy này:")
        st.dataframe(warning_machines[['MÃ_MÁY', 'Days_Since']].rename(columns={'Days_Since': 'Số ngày đã chạy ổn định'}))
    else:
        st.success("✅ Hiện tại các thiết bị vẫn đang trong vòng đời an toàn.")
