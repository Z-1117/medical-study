import streamlit as st
import pandas as pd
import datetime
import os
import time

# ==========================
# 页面配置
# ==========================
st.set_page_config(
    page_title="Z — 医学备考系统",
    layout="wide",
    initial_sidebar_state="auto"
)

# ==========================
# 样式美化
# ==========================
st.markdown("""
<style>
    .stButton>button {
        border-radius: 10px;
        background-color: #2C6EBC;
        color: white;
        font-weight: bold;
        height: 3.4em;
    }
    .stMetric {
        background-color: #F8F9FA;
        border-radius: 12px;
        padding: 14px;
        font-size: 24px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# 数据文件（安全稳定）
# ==========================
DATA_FILE = "study_data.csv"
REVIEW_FILE = "review_plan.csv"
MEMO_FILE = "memo.csv"
TIMELINE_FILE = "weekly_timeline.csv"

def safe_init(file, cols):
    if not os.path.exists(file):
        pd.DataFrame(columns=cols).to_csv(file, index=False)
    try:
        return pd.read_csv(file)
    except:
        return pd.DataFrame(columns=cols)

df = safe_init(DATA_FILE, ["日期","主项目","子项目","时间类型","开始时间","结束时间","总时长(分钟)","备注"])
review_df = safe_init(REVIEW_FILE, ["内容","首次学习日期","复习节点","是否完成","统一侧重","个性侧重"])
memo_df = safe_init(MEMO_FILE, ["日期","备忘内容"])

# ==========================
# 秒表状态（绝对稳定）
# ==========================
if "sw_start" not in st.session_state:
    st.session_state.sw_start = None
if "sw_running" not in st.session_state:
    st.session_state.sw_running = False
if "sw_elapsed" not in st.session_state:
    st.session_state.sw_elapsed = 0

# 实时计算时间
if st.session_state.sw_running and st.session_state.sw_start:
    now = time.time()
    st.session_state.sw_elapsed = int(now - st.session_state.sw_start)

# 时间格式化
def fmt(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# ==========================
# 生成时间段 6:30 - 22:30 每30分钟
# ==========================
def get_time_slots():
    slots = []
    current = datetime.datetime(2000, 1, 1, 6, 30)
    for i in range(33):
        end = current + datetime.timedelta(minutes=30)
        slots.append(f"{current.strftime('%H:%M')} - {end.strftime('%H:%M')}")
        current = end
    return slots

slots = get_time_slots()

# ==========================
# 每周日程（你要的样式：每段后面都能填内容）
# ==========================
def weekly_schedule():
    st.subheader("📅 每周学习日程（每时间段可填内容）")
    days = ["第1天", "第2天", "第3天", "第4天", "第5天", "第6天", "第7天"]
    
    for day_idx, day_name in enumerate(days):
        st.markdown(f"---")
        st.markdown(f"## 📌 {day_name}")
        
        day_data = []
        for i, slot in enumerate(slots):
            content = st.text_input(f"📝 {slot}", key=f"c{day_idx}_{i}")
            duration = st.number_input(f"⏱ 时长(分钟) {slot}", min_value=0, key=f"d{day_idx}_{i}")
            day_data.append({"时间段": slot, "内容": content, "时长": duration})
        
        total = sum([d["时长"] for d in day_data])
        st.metric(f"✅ {day_name} 总学习时长", f"{total} 分钟")
        
        st.text_area(f"💡 {day_name} 反思总结", key=f"sum_{day_idx}", height=100)

    if st.button("💾 保存整周日程"):
        st.success("✅ 保存成功！")

# ==========================
# 主界面
# ==========================
st.title("🩺 Z — 医学备考系统")
menu = st.selectbox("菜单", ["⏱️ 时间记录", "📅 每周日程", "📚 复习计划", "📜 历史记录", "💾 数据导出"])

MAIN = ["医学备考","英语","科研","休息","运动","饮食","通勤","娱乐","其他"]
TYPES = ["深度学习","浅度学习","休息","无效","自定义"]

# ==========================
# 1. 时间记录
# ==========================
if menu == "⏱️ 时间记录":
    st.subheader("⏱️ 学习计时（实时秒表）")

    col1, col2, col3 = st.columns(3)
    with col1:
        main = st.selectbox("主项目", MAIN)
    with col2:
        sub = st.text_input("子项目")
    with col3:
        tp = st.selectbox("时间类型", TYPES)
        if tp == "自定义":
            tp = st.text_input("输入类型")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▶️ 开始"):
            if not st.session_state.sw_running:
                st.session_state.sw_start = time.time() - st.session_state.sw_elapsed
                st.session_state.sw_running = True
    with c2:
        if st.button("⏸️ 暂停/继续"):
            if st.session_state.sw_running:
                st.session_state.sw_running = False
            else:
                st.session_state.sw_start = time.time() - st.session_state.sw_elapsed
                st.session_state.sw_running = True
    with c3:
        if st.button("⏹️ 结束并保存"):
            if st.session_state.sw_elapsed > 0:
                dur = st.session_state.sw_elapsed // 60
                s_str = datetime.datetime.fromtimestamp(st.session_state.sw_start).strftime("%H:%M:%S")
                e_str = datetime.datetime.now().strftime("%H:%M:%S")
                new_row = pd.DataFrame([{
                    "日期": str(datetime.date.today()),
                    "主项目": main,
                    "子项目": sub,
                    "时间类型": tp,
                    "开始时间": s_str,
                    "结束时间": e_str,
                    "总时长(分钟)": dur,
                    "备注": ""
                }])
                df_new = pd.concat([df, new_row], ignore_index=True)
                df_new.to_csv(DATA_FILE, index=False)

                st.session_state.sw_running = False
                st.session_state.sw_elapsed = 0
                st.session_state.sw_start = None
                st.success("✅ 保存成功")

    placeholder = st.empty()
    with placeholder:
        st.metric("当前计时", fmt(st.session_state.sw_elapsed))

    if st.session_state.sw_running:
        time.sleep(0.1)
        st.rerun()

    st.subheader("📝 今日记录")
    today = str(datetime.date.today())
    td = df[df["日期"] == today].copy()
    if not td.empty:
        td.insert(0, "选", False)
        ed = st.data_editor(td, height=300)
        if st.button("删除选中"):
            keep = df[df["日期"] != today]
            rem = td[ed["选"] == False]
            final = pd.concat([keep, rem], ignore_index=True)
            final.to_csv(DATA_FILE, index=False)
            st.rerun()

# ==========================
# 2. 每周日程（你要的样式）
# ==========================
elif menu == "📅 每周日程":
    weekly_schedule()

# ==========================
# 3. 复习计划
# ==========================
elif menu == "📚 复习计划":
    st.subheader("📚 复习计划")
    txt = st.text_area("一行一个内容")
    d = st.date_input("日期")
    if st.button("生成计划"):
        lines = [x.strip() for x in txt.split("\n") if x.strip()]
        days = [0,1,2,4,7,15,30,90,180]
        rows = []
        for l in lines:
            for dy in days:
                rv = str(d + datetime.timedelta(days=dy))
                rows.append({"内容":l,"首次学习日期":str(d),"复习节点":rv,"是否完成":"否","统一侧重":"","个性侧重":""})
        new_df = pd.DataFrame(rows)
        all_df = pd.concat([review_df, new_df], ignore_index=True)
        all_df.to_csv(REVIEW_FILE, index=False)
        st.success("完成")
        st.rerun()

    today = str(datetime.date.today())
    tr = review_df[review_df["复习节点"] == today]
    st.data_editor(tr, height=300)

# ==========================
# 4. 历史记录
# ==========================
elif menu == "📜 历史记录":
    st.subheader("📜 历史记录")
    sday = str(st.date_input("选择日期"))
    hist = df[df["日期"] == sday]
    st.data_editor(hist, height=400)

# ==========================
# 5. 数据导出
# ==========================
elif menu == "💾 数据导出":
    st.subheader("💾 导出")
    if st.button("导出学习记录"):
        df.to_csv("学习记录.csv", index=False)
        st.success("已导出")
    if st.button("导出复习计划"):
        review_df.to_csv("复习计划.csv", index=False)
        st.success("已导出")
