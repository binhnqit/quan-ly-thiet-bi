# ui/ceo_view.py
import streamlit as st
import plotly.express as px
from config import ORANGE_PALETTE

def render_dashboard(df, kpis):
    """Giao diện chính hiển thị các chỉ số quan trọng"""
    st.title("🚀 BẢNG ĐIỀU HÀNH CHI PHÍ KỸ THUẬT")
    
    # 1. Hàng KPI Top-level
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng chi phí", f"{kpis['total_cost']:,.0f}đ", delta="-5% so với tháng trước")
    with col2:
        st.metric("Số ca xử lý", f"{kpis['total_cases']} ca")
    with col3:
        st.metric("Trung bình/Ca", f"{kpis['cost_per_case']:,.0f}đ")
    with col4:
        efficiency = "Ổn định" if kpis['cost_per_case'] < 2000000 else "Cần chú ý"
        st.metric("Trạng thái vận hành", efficiency)

    st.divider()

    # 2. Khu vực Biểu đồ Xu hướng & Phân vùng
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📈 Xu hướng chi phí theo tháng")
        monthly_df = df.groupby('month')['cost'].sum().reset_index()
        fig = px.area(monthly_df, x='month', y='cost', 
                     color_discrete_sequence=[ORANGE_PALETTE[0]])
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.subheader("📍 Tỷ trọng theo vùng")
        fig_pie = px.pie(df, names='region', values='cost', 
                        hole=0.5, color_discrete_sequence=ORANGE_PALETTE)
        st.plotly_chart(fig_pie, use_container_width=True)

def alert_room(proposals):
    """Phòng điều hành AI - Nơi Sếp ra quyết định nhanh"""
    st.write("---")
    st.subheader("🤖 AI STRATEGIC ADVISOR")
    
    if not proposals:
        st.success("✅ Hệ thống đang vận hành tốt. Chưa phát hiện rủi ro cần xử lý ngay.")
        return

    # Giao diện dạng thẻ (Cards) cho từng đề xuất
    for i, p in enumerate(proposals):
        with st.container(border=True):
            col_txt, col_btn = st.columns([3, 1])
            
            with col_txt:
                st.markdown(f"### 🚨 Đề xuất: **{p['action']}**")
                st.markdown(f"**Đối tượng:** Máy `{p['machine_id']}`")
                st.caption(f"**Lý do:** {p['reason']}")
                st.progress(p['confidence'], text=f"Độ tin cậy của AI: {int(p['confidence']*100)}%")
            
            with col_btn:
                st.write("") # Tạo khoảng trống
                if st.button("✅ PHÊ DUYỆT", key=f"approve_{i}", use_container_width=True):
                    # Gọi hàm từ governance/decision_log.py
                    st.toast(f"Đã ghi nhận phê duyệt cho máy {p['machine_id']}")
                
                if st.button("❌ BỎ QUA", key=f"ignore_{i}", use_container_width=True):
                    st.info("Đã từ chối đề xuất.")

def render_deep_dive(df):
    """Phần chi tiết dành cho cấp quản lý chuyên sâu"""
    with st.expander("🔍 Xem chi tiết bảng dữ liệu linh kiện"):
        df_parts = df.groupby('part').agg({
            'cost': 'sum',
            'machine_id': 'count'
        }).rename(columns={'machine_id': 'Số lần thay'}).sort_values('cost', ascending=False)
        st.table(df_parts.style.format("{:,.0f}đ", subset=['cost']))
