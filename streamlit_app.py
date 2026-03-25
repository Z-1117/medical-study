import streamlit as st
import pandas as pd
import datetime
import os
import time
import sqlite3
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==============================================
# 系统基础配置
# ==============================================
st.set_page_config(
    page_title="Z — 医学备考系统",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="auto",
)

# ==============================================
# 全局UI样式
# ==============================================
st.markdown("""
<style>
    .stButton>button {
        border-radius: 12px;
        background-color: #2C6EBC;
        color: white;
        font-weight: bold;
        height: 3.2em;
        font-size: 14px;
        margin: 4px 0px;
    }
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 14px;
        padding: 16px;
        color: white;
        text-align: center;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1 {
        color: #2C3E50;
        font-size: 28px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================
# 数据库管理
# ==============================================
class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
    
    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_file, check_same_thread=False, timeout=10)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            st.error(f"数据库连接失败: {e}")
            return None
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        conn = self.get_connection()
        if not conn:
            return None if fetch_one or fetch_all else False
        
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.lastrowid
            
            return result
        except Exception as e:
            st.error(f"数据库操作失败: {e}")
            return None if fetch_one or fetch_all else False
        finally:
            conn.close()

db_manager = DatabaseManager("study_system.db")

# ==============================================
# 初始化数据库
# ==============================================
def init_database():
    queries = [
        '''CREATE TABLE IF NOT EXISTS study_records
           (id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, main_project TEXT, sub_project TEXT,
            time_type TEXT, start_time TEXT, end_time TEXT,
            duration_min INTEGER, remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''',
        
        '''CREATE TABLE IF NOT EXISTS review_plans
           (id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT, first_learn_date TEXT, review_date TEXT,
            finished TEXT DEFAULT '否', common_focus TEXT, 
            personal_focus TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''',
        
        '''CREATE TABLE IF NOT EXISTS memos
           (id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''',
        
        '''CREATE TABLE IF NOT EXISTS settings
           (id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT, reminder_enabled INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''',
        
        '''CREATE INDEX IF NOT EXISTS idx_study_date ON study_records(date)''',
        '''CREATE INDEX IF NOT EXISTS idx_review_date ON review_plans(review_date)'''
    ]
    
    for query in queries:
        db_manager.execute_query(query)

init_database()

# ==============================================
# 秒表状态
# ==============================================
if "stopwatch_start_ts" not in st.session_state:
    st.session_state.stopwatch_start_ts = None
if "stopwatch_running" not in st.session_state:
    st.session_state.stopwatch_running = False
if "stopwatch_elapsed" not in st.session_state:
    st.session_state.stopwatch_elapsed = 0

def format_time(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def update_stopwatch():
    if st.session_state.stopwatch_running and st.session_state.stopwatch_start_ts:
        st.session_state.stopwatch_elapsed = int(time.time() - st.session_state.stopwatch_start_ts)

# ==============================================
# 邮件发送
# ==============================================
def send_email(to_email, subject, content):
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender = os.getenv("EMAIL_SENDER")
        password = os.getenv("EMAIL_PASSWORD")
        
        if not sender or not password:
            return False, "邮件配置未设置"
        
        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email
        
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
        
        return True, "发送成功"
    except Exception as e:
        return False, str(e)

# ==============================================
# 辅助函数
# ==============================================
def safe_read_sql(query, params=None):
    conn = db_manager.get_connection()
    if not conn:
        return pd.DataFrame()
    try:
        if params:
            return pd.read_sql(query, conn, params=params)
        else:
            return pd.read_sql(query, conn)
    finally:
        conn.close()

# ==============================================
# 主界面
# ==============================================
st.title("🩺 Z — 医学备考系统")
st.caption("专业版 | 实时秒表 | 数据持久化")

# 侧边栏
with st.sidebar:
    st.header("📊 今日统计")
    today = str(datetime.date.today())
    
    df_today = safe_read_sql(
        "SELECT SUM(duration_min) as total FROM study_records WHERE date = ?",
        (today,)
    )
    total_min = df_today["total"].iloc[0] if not df_today.empty and df_today["total"].iloc[0] else 0
    st.metric("今日学习", f"{total_min} 分钟")
    
    review_count = db_manager.execute_query(
        "SELECT COUNT(*) as c FROM review_plans WHERE review_date = ? AND finished='否'",
        (today,), fetch_one=True
    )
    st.metric("待复习", f"{review_count['c'] if review_count else 0} 项")

st.divider()

# 菜单
menu = st.selectbox("功能菜单", [
    "⏱️ 学习计时",
    "📚 复习计划",
    "📜 历史记录",
    "📝 备忘录",
    "💾 数据导出",
    "🔔 推送设置"
])

# ==============================================
# 学习计时
# ==============================================
if menu == "⏱️ 学习计时":
    st.subheader("⏱️ 学习计时")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        main_project = st.selectbox("主项目", ["医学备考", "英语", "科研", "休息", "运动", "其他"])
    with col2:
        sub_project = st.text_input("子项目", placeholder="如：生理学")
    with col3:
        time_type = st.selectbox("时间类型", ["深度学习", "浅度学习", "休息", "其他"])
    
    update_stopwatch()
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("▶️ 开始", use_container_width=True):
            if not st.session_state.stopwatch_running:
                st.session_state.stopwatch_start_ts = time.time() - st.session_state.stopwatch_elapsed
                st.session_state.stopwatch_running = True
                st.rerun()
    
    with col_btn2:
        if st.button("⏸️ 暂停", use_container_width=True):
            if st.session_state.stopwatch_running:
                update_stopwatch()
                st.session_state.stopwatch_running = False
                st.rerun()
    
    with col_btn3:
        if st.button("💾 保存", use_container_width=True):
            if st.session_state.stopwatch_elapsed > 0:
                duration_min = st.session_state.stopwatch_elapsed // 60
                if duration_min > 0:
                    start_str = datetime.datetime.fromtimestamp(
                        st.session_state.stopwatch_start_ts
                    ).strftime("%H:%M:%S")
                    end_str = datetime.datetime.now().strftime("%H:%M:%S")
                    
                    db_manager.execute_query(
                        '''INSERT INTO study_records 
                           (date, main_project, sub_project, time_type, 
                            start_time, end_time, duration_min, remark)
                           VALUES (?,?,?,?,?,?,?,?)''',
                        (today, main_project, sub_project, time_type,
                         start_str, end_str, duration_min, "")
                    )
                    
                    st.session_state.stopwatch_running = False
                    st.session_state.stopwatch_elapsed = 0
                    st.session_state.stopwatch_start_ts = None
                    st.success(f"✅ 保存成功！学习 {duration_min} 分钟")
                    time.sleep(1)
                    st.rerun()
    
    st.metric("当前计时", format_time(st.session_state.stopwatch_elapsed))
    
    # 今日记录
    st.divider()
    st.subheader("今日记录")
    df_today_records = safe_read_sql(
        "SELECT * FROM study_records WHERE date = ? ORDER BY id DESC",
        (today,)
    )
    if not df_today_records.empty:
        st.dataframe(df_today_records, use_container_width=True)

# ==============================================
# 复习计划
# ==============================================
elif menu == "📚 复习计划":
    st.subheader("📚 艾宾浩斯复习计划")
    
    col1, col2 = st.columns(2)
    with col1:
        contents = st.text_area("复习内容（一行一个）", height=150)
    with col2:
        start_date = st.date_input("首次学习日期")
        focus = st.text_input("个性侧重")
    
    if st.button("生成复习计划", use_container_width=True):
        lines = [x.strip() for x in contents.split("\n") if x.strip()]
        days = [0, 1, 2, 4, 7, 15, 30, 90, 180]
        added = 0
        
        for content in lines:
            for d in days:
                review_date = str(start_date + datetime.timedelta(days=d))
                existing = db_manager.execute_query(
                    "SELECT id FROM review_plans WHERE content=? AND review_date=?",
                    (content, review_date), fetch_one=True
                )
                if not existing:
                    db_manager.execute_query(
                        '''INSERT INTO review_plans 
                           (content, first_learn_date, review_date, finished, personal_focus)
                           VALUES (?,?,?,?,?)''',
                        (content, str(start_date), review_date, "否", focus)
                    )
                    added += 1
        
        st.success(f"✅ 生成 {added} 条计划")
        time.sleep(1)
        st.rerun()
    
    st.divider()
    st.subheader("今日复习")
    df_review = safe_read_sql(
        "SELECT * FROM review_plans WHERE review_date = ?",
        (today,)
    )
    if not df_review.empty:
        edited = st.data_editor(df_review, use_container_width=True, height=300)
        if st.button("保存修改"):
            for _, row in edited.iterrows():
                db_manager.execute_query(
                    "UPDATE review_plans SET finished=? WHERE id=?",
                    (row["finished"], row["id"])
                )
            st.success("已保存")
            st.rerun()
    else:
        st.info("今日无复习任务")

# ==============================================
# 历史记录
# ==============================================
elif menu == "📜 历史记录":
    st.subheader("历史记录")
    date = st.date_input("选择日期")
    df_hist = safe_read_sql(
        "SELECT * FROM study_records WHERE date = ? ORDER BY start_time",
        (str(date),)
    )
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        total = df_hist["duration_min"].sum()
        st.metric("当日总计", f"{total} 分钟 ({total/60:.1f} 小时)")
    else:
        st.info("无记录")

# ==============================================
# 备忘录
# ==============================================
elif menu == "📝 备忘录":
    st.subheader("备忘录")
    
    new_memo = st.text_input("新备忘")
    if st.button("添加"):
        if new_memo.strip():
            db_manager.execute_query(
                "INSERT INTO memos (date, content) VALUES (?,?)",
                (today, new_memo.strip())
            )
            st.rerun()
    
    st.divider()
    df_memos = safe_read_sql("SELECT * FROM memos ORDER BY date DESC, id DESC")
    if not df_memos.empty:
        for _, memo in df_memos.iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"📌 {memo['date']}: {memo['content']}")
            with col2:
                if st.button("删除", key=f"del_{memo['id']}"):
                    db_manager.execute_query("DELETE FROM memos WHERE id=?", (memo["id"],))
                    st.rerun()

# ==============================================
# 数据导出
# ==============================================
elif menu == "💾 数据导出":
    st.subheader("数据导出")
    
    if st.button("导出学习记录"):
        df = safe_read_sql("SELECT * FROM study_records")
        df.to_csv("学习记录.csv", index=False, encoding="utf-8-sig")
        st.success("已导出")
    
    if st.button("导出复习计划"):
        df = safe_read_sql("SELECT * FROM review_plans")
        df.to_csv("复习计划.csv", index=False, encoding="utf-8-sig")
        st.success("已导出")
    
    if st.button("导出备忘录"):
        df = safe_read_sql("SELECT * FROM memos")
        df.to_csv("备忘录.csv", index=False, encoding="utf-8-sig")
        st.success("已导出")

# ==============================================
# 推送设置
# ==============================================
elif menu == "🔔 推送设置":
    st.subheader("推送设置")
    
    settings = db_manager.execute_query(
        "SELECT email, reminder_enabled FROM settings LIMIT 1",
        fetch_one=True
    )
    
    email = st.text_input("接收邮箱", value=settings["email"] if settings else "")
    enabled = st.checkbox("启用推送", value=bool(settings["reminder_enabled"]) if settings else False)
    
    if st.button("保存设置"):
        db_manager.execute_query("DELETE FROM settings")
        db_manager.execute_query(
            "INSERT INTO settings (email, reminder_enabled) VALUES (?,?)",
            (email, 1 if enabled else 0)
        )
        st.success("设置已保存")
    
    if enabled and email:
        st.divider()
        if st.button("发送测试邮件"):
            success, msg = send_email(email, "测试邮件", "您的备考系统运行正常")
            if success:
                st.success("测试邮件已发送")
            else:
                st.error(f"发送失败: {msg}")

st.divider()
st.caption("© Z医学备考系统 | 数据本地存储 | 安全稳定")
