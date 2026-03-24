import streamlit as st
import pandas as pd
import datetime
import os
import time

# 页面设置（美化）
st.set_page_config(
    page_title="Z — 医学备考系统",
    layout="wide",
    initial_sidebar_state="auto"
)

# 自定义CSS美化
st.markdown("""
<style>
    .stButton>button {
        border-radius: 8px;
        background-color: #2c6ecb;
        color: white;
        font-weight: bold;
    }
    .stDataEditor {
        border-radius: 10px;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stMetric {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 数据文件
DATA_FILE = "study_data.csv"
REVIEW_FILE = "review_plan.csv"
MEMO_FILE = "memo.csv"

# 初始化学习数据
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=[
        "日期", "主项目", "子项目", "时间类型", "开始时间", "结束时间", "总时长(分钟)", "备注"
    ])
    df.to_csv(DATA_FILE, index=False)

# 初始化复习计划（兼容旧数据）
if not os.path.exists(REVIEW_FILE):
    review_df = pd.DataFrame(columns=[
        "内容", "首次学习日期", "复习节点", "是否完成", "统一侧重", "个性侧重"
    ])
    review_df.to_csv(REVIEW_FILE, index=False)
else:
    review_df = pd.read_csv(REVIEW_FILE)
    if "个性侧重" not in review_df.columns:
        review_df["个性侧重"] = ""
    if "统一侧重" not in review_df.columns:
        review_df["统一侧重"] = ""

# 初始化备忘录
if not os.path.exists(MEMO_FILE):
    memo_df = pd.DataFrame(columns=["日期", "备忘内容"])
    memo_df.to_csv(MEMO_FILE, index=False)

# 加载数据
df = pd.read_csv(DATA_FILE)
memo_df = pd.read_csv(MEMO_FILE)

# 清洗数据
review_df["内容"] = review_df["内容"].fillna("").astype(str)

# 标题
st.title("🩺 Z — 医学备考系统")

# 菜单
menu = st.selectbox("📋 选择功能", ["⏱️ 时间记录", "📚 复习计划", "📜 历史记录", "💾 数据导出"])

# 主项目
main_projects = ["医学备考", "英语", "科研", "休息", "运动", "饮食", "通勤", "娱乐", "其他"]
time_types = ["深度学习", "浅度学习", "休息", "无效", "自定义"]

# 秒表状态（纯秒表逻辑，无负数）
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "running" not in st.session_state:
    st.session_state.running = False
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

# 实时秒表（修复：实时刷新）
placeholder = st.empty()  # 实时显示用

# 实时刷新循环
while True:
    if st.session_state.running and st.session_state.start_time:
        elapsed = datetime.datetime.now() - st.session_state.start_time
        st.session_state.elapsed_seconds = int(elapsed.total_seconds())

    # 格式化时间
    def format_time(seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    # 实时显示
    with placeholder.container():
        st.metric("当前计时", format_time(st.session_state.elapsed_seconds))

    time.sleep(0.1)  # 100ms 刷新一次，流畅不卡顿

    # ====================== 时间记录 ======================
    if menu == "⏱️ 时间记录":
        st.subheader("⏱️ 时间记录")

        col1, col2, col3 = st.columns(3)
        with col1:
            main_project = st.selectbox("主项目", main_projects, key="main")
        with col2:
            sub_project = st.text_input("子项目", key="sub")
        with col3:
            time_type = st.selectbox("时间类型", time_types, key="type")
            if time_type == "自定义":
                time_type = st.text_input("自定义类型", key="custom_type")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("▶️ 开始", key="start"):
                st.session_state.start_time = datetime.datetime.now()
                st.session_state.running = True
                st.session_state.elapsed_seconds = 0
        with col_b:
            if st.button("⏸️ 暂停 / ▶️ 继续", key="pause"):
                if st.session_state.running:
                    st.session_state.running = False
                else:
                    st.session_state.start_time = datetime.datetime.now() - datetime.timedelta(seconds=st.session_state.elapsed_seconds)
                    st.session_state.running = True
        with col_c:
            if st.button("⏹️ 结束", key="end"):
                if st.session_state.start_time:
                    duration_min = st.session_state.elapsed_seconds // 60
                    new_row = pd.DataFrame({
                        "日期": [str(datetime.date.today())],
                        "主项目": [main_project],
                        "子项目": [sub_project],
                        "时间类型": [time_type],
                        "开始时间": [st.session_state.start_time.strftime("%H:%M:%S")],
                        "结束时间": [datetime.datetime.now().strftime("%H:%M:%S")],
                        "总时长(分钟)": [duration_min],
                        "备注": [""]
                    })
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.session_state.start_time = None
                    st.session_state.running = False
                    st.session_state.elapsed_seconds = 0

        st.subheader("📝 今日记录（双击可编辑）")
        today = str(datetime.date.today())
        today_df = df[df["日期"] == today].copy()
        today_df.insert(0, "✅ 选择", False)
        edited_today = st.data_editor(today_df, use_container_width=True, height=300, num_rows="dynamic")
        if any(edited_today["✅ 选择"]):
            if st.button("🗑️ 删除选中行"):
                df = df.drop(index=today_df[edited_today["✅ 选择"]].index).reset_index(drop=True)
                df.to_csv(DATA_FILE, index=False)
                st.rerun()

        # 备忘区
        st.subheader("📌 今日备忘（双击可编辑）")
        today_memo = memo_df[memo_df["日期"] == today].copy()
        today_memo.insert(0, "✅ 选择", False)
        edited_memo = st.data_editor(today_memo, use_container_width=True, height=200, num_rows="dynamic")
        if any(edited_memo["✅ 选择"]):
            if st.button("🗑️ 删除选中备忘"):
                memo_df = memo_df.drop(index=today_memo[edited_memo["✅ 选择"]].index).reset_index(drop=True)
                memo_df.to_csv(MEMO_FILE, index=False)
                st.rerun()
        if st.button("➕ 添加新备忘"):
            new_memo = pd.DataFrame({"日期": [today], "备忘内容": ["新备忘"]})
            memo_df = pd.concat([memo_df, new_memo], ignore_index=True)
            memo_df.to_csv(MEMO_FILE, index=False)
            st.rerun()

    # ====================== 复习计划 ======================
    elif menu == "📚 复习计划":
        st.subheader("📚 复习计划")

        # 统一侧重
        st.subheader("🎯 统一复习侧重")
        default_focus = {
            0: st.text_input("第0天", value="理解框架"),
            1: st.text_input("第1天", value="回忆关键词"),
            2: st.text_input("第2天", value="复述要点"),
            4: st.text_input("第4天", value="查漏补缺"),
            7: st.text_input("第7天", value="系统回顾"),
            15: st.text_input("第15天", value="综合应用"),
            30: st.text_input("第30天", value="深度理解"),
            90: st.text_input("第90天", value="长期巩固"),
            180: st.text_input("第180天", value="最终强化")
        }

        # 批量添加
        st.subheader("➕ 批量添加复习内容")
        content_list = st.text_area("内容（一行一个）")
        custom_date = st.date_input("首次学习日期")
        personal_focus = st.text_input("个性侧重")

        if st.button("✅ 批量添加"):
            contents = [c.strip() for c in content_list.split("\n") if c.strip()]
            review_days = [0,1,2,4,7,15,30,90,180]
            new_rows = []
            for c in contents:
                for d in review_days:
                    review_date = custom_date + datetime.timedelta(days=d)
                    new_rows.append({
                        "内容": c,
                        "首次学习日期": str(custom_date),
                        "复习节点": str(review_date),
                        "是否完成": "否",
                        "统一侧重": default_focus[d],
                        "个性侧重": personal_focus
                    })
            review_df = pd.concat([review_df, pd.DataFrame(new_rows)], ignore_index=True)
            review_df.to_csv(REVIEW_FILE, index=False)
            st.success("添加成功！")
            st.rerun()

        # 今日复习
        st.subheader("📅 今日复习（双击可编辑）")
        today_str = str(datetime.date.today())
        today_review = review_df[review_df["复习节点"] == today_str].copy()
        today_review.insert(0, "✅ 选择", False)
        edited_today_review = st.data_editor(today_review, use_container_width=True, height=300, num_rows="dynamic")
        if any(edited_today_review["✅ 选择"]):
            if st.button("🗑️ 删除选中复习任务"):
                review_df = review_df.drop(index=today_review[edited_today_review["✅ 选择"]].index).reset_index(drop=True)
                review_df.to_csv(REVIEW_FILE, index=False)
                st.rerun()

        # 完整复习计划
        st.subheader("📋 完整复习计划（双击可编辑）")
        review_df_edit = review_df.copy()
        review_df_edit.insert(0, "✅ 选择", False)
        edited_review = st.data_editor(review_df_edit, use_container_width=True, height=400, num_rows="dynamic")
        if any(edited_review["✅ 选择"]):
            if st.button("🗑️ 删除选中复习计划"):
                review_df = review_df.drop(index=review_df_edit[edited_review["✅ 选择"]].index).reset_index(drop=True)
                review_df.to_csv(REVIEW_FILE, index=False)
                st.rerun()

    # ====================== 历史记录 ======================
    elif menu == "📜 历史记录":
        st.subheader("📜 历史记录（双击可编辑）")
        selected_date = st.date_input("选择日期")
        selected_date_str = str(selected_date)
        history_df = df[df["日期"] == selected_date_str].copy()
        history_df.insert(0, "✅ 选择", False)
        edited_history = st.data_editor(history_df, use_container_width=True, height=400, num_rows="dynamic")
        if any(edited_history["✅ 选择"]):
            if st.button("🗑️ 删除选中历史记录"):
                df = df.drop(index=history_df[edited_history["✅ 选择"]].index).reset_index(drop=True)
                df.to_csv(DATA_FILE, index=False)
                st.rerun()

    # ====================== 数据导出 ======================
    elif menu == "💾 数据导出":
        st.subheader("💾 数据导出")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if st.button("📥 导出学习记录到桌面"):
            df.to_csv(os.path.join(desktop, "学习记录.csv"), index=False)
            st.success("已保存到桌面：学习记录.csv")
        if st.button("📥 导出复习计划到桌面"):
            review_df.to_csv(os.path.join(desktop, "复习计划.csv"), index=False)
            st.success("已保存到桌面：复习计划.csv")

    break  # 只循环一次，避免卡死
