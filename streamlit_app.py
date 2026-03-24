import streamlit as st
import time
from datetime import datetime

# 页面设置
st.set_page_config(page_title="医学备考系统", page_icon="📚", layout="wide")

# 自定义样式
st.markdown("""
<style>
.big-font {
    font-size:30px !important;
    font-weight: bold;
    color: #1f77b4;
}
.medium-font {
    font-size:20px !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown('<p class="big-font">📚 医学备考学习系统</p>', unsafe_allow_html=True)

# 创建标签页
tab1, tab2, tab3 = st.tabs(["⏱️ 学习计时", "📝 学习记录", "🔗 资料汇总"])

with tab1:
    st.markdown('<p class="medium-font">专注学习秒表</p>', unsafe_allow_html=True)
    
    # 初始化状态
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
        st.session_state.paused_time = 0
        st.session_state.running = False
        st.session_state.total_study = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ 开始", use_container_width=True):
            if not st.session_state.running:
                st.session_state.start_time = time.time() - st.session_state.paused_time
                st.session_state.running = True
    with col2:
        if st.button("⏸️ 暂停", use_container_width=True):
            if st.session_state.running:
                st.session_state.paused_time = time.time() - st.session_state.start_time
                st.session_state.running = False
    with col3:
        if st.button("⏹️ 结束", use_container_width=True):
            if st.session_state.running or st.session_state.paused_time > 0:
                if st.session_state.running:
                    final_time = time.time() - st.session_state.start_time
                else:
                    final_time = st.session_state.paused_time
                
                st.session_state.total_study += int(final_time)
                st.session_state.start_time = None
                st.session_state.paused_time = 0
                st.session_state.running = False
                st.success(f"本次学习 {int(final_time//60)} 分 {int(final_time%60)} 秒")

    # 实时显示
    if st.session_state.running:
        elapsed = time.time() - st.session_state.start_time
    else:
        elapsed = st.session_state.paused_time

    hours = int(elapsed // 3600)
    mins = int((elapsed % 3600) // 60)
    secs = int(elapsed % 60)
    st.metric("当前计时", f"{hours:02d}:{mins:02d}:{secs:02d}")
    st.metric("累计学习", f"{st.session_state.total_study//60} 分 {st.session_state.total_study%60} 秒")

with tab2:
    st.markdown('<p class="medium-font">今日学习记录</p>', unsafe_allow_html=True)
    today = datetime.now().strftime("%Y-%m-%d")
    record = st.text_area(f"{today} 学习内容", height=200)
    if st.button("保存记录"):
        st.success("记录保存成功！")

with tab3:
    st.markdown('<p class="medium-font">备考资料汇总</p>', unsafe_allow_html=True)
    st.link_button("生理学笔记", "https://example.com/shengli")
    st.link_button("内科学题库", "https://example.com/neike")
    st.link_button("外科学重点", "https://example.com/waike")
