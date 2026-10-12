
import streamlit as st
import sqlite3
import random
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------- APP CONFIG ----------------
st.set_page_config(
    page_title="NEUROMIND AI",
    page_icon="🧠",
    layout="wide"
)

DB_FILE = "neuromind.db"

# ---------------- PREMIUM UI ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020 0%, #19132e 55%, #261342 100%);
    color: #f8fafc;
}
[data-testid="stSidebar"] {
    background: #100d20;
}
h1, h2, h3 {
    color: #e9d5ff !important;
}
p, label, li {
    color: #e2e8f0;
}
div.stButton > button {
    background: linear-gradient(90deg, #9333ea, #6d28d9);
    color: white;
    border: 1px solid #a855f7;
    border-radius: 12px;
    min-height: 42px;
    font-weight: 600;
}
div.stButton > button:hover {
    border-color: #e9d5ff;
    color: white;
}
[data-testid="stMetric"] {
    background: rgba(147, 51, 234, 0.12);
    border: 1px solid rgba(192, 132, 252, 0.25);
    border-radius: 15px;
    padding: 16px;
}
div[data-testid="stForm"] {
    background: rgba(255,255,255,0.03);
    padding: 20px;
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
def connect_db():
    return sqlite3.connect(DB_FILE)

def setup_database():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                username TEXT PRIMARY KEY,
                level INTEGER NOT NULL DEFAULT 1,
                joined_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                challenge TEXT NOT NULL,
                result TEXT NOT NULL,
                points INTEGER NOT NULL,
                level INTEGER NOT NULL,
                played_at TEXT NOT NULL
            )
        """)

def register_student(username):
    with connect_db() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO students
            (username, level, joined_at)
            VALUES (?, 1, ?)
        """, (username, datetime.now().isoformat(timespec="seconds")))

def get_student_level(username):
    with connect_db() as conn:
        row = conn.execute(
            "SELECT level FROM students WHERE username = ?",
            (username,)
        ).fetchone()
    return row[0] if row else 1

def save_round(username, challenge, correct, points, level):
    result = "Correct" if correct else "Incorrect"
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO rounds
            (username, challenge, result, points, level, played_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            username,
            challenge,
            result,
            points,
            level,
            datetime.now().isoformat(timespec="seconds")
        ))

def update_student_level(username, level):
    with connect_db() as conn:
        conn.execute(
            "UPDATE students SET level = ? WHERE username = ?",
            (level, username)
        )

def load_history(username=None):
    with connect_db() as conn:
        if username:
            df = pd.read_sql_query("""
                SELECT challenge AS Challenge,
                       result AS Result,
                       points AS Score,
                       level AS Level,
                       played_at AS Time
                FROM rounds
                WHERE username = ?
                ORDER BY id DESC
            """, conn, params=(username,))
        else:
            df = pd.read_sql_query("""
                SELECT username AS Student,
                       SUM(points) AS Score,
                       COUNT(*) AS Rounds,
                       MAX(played_at) AS Last_Played
                FROM rounds
                GROUP BY username
                ORDER BY Score DESC, Rounds DESC
            """, conn)
    return df

setup_database()

# ---------------- SESSION STATE ----------------
defaults = {
    "username": "",
    "number_target": None,
    "number_visible": False,
    "number_attempt": 0,
    "pattern_target": None,
    "pattern_visible": False,
    "pattern_attempt": 0,
    "notice": ""
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------- LOGIN ----------------
if not st.session_state.username:
    st.title("🧠 NEUROMIND AI")
    st.subheader("Your Personal Memory Challenge Lab")
    st.write("Train your memory. Challenge yourself. Track your progress.")

    st.info(
        "Student demo login: enter your name. "
        "This is name-based identification, not password-secured authentication."
    )

    with st.form("login_form"):
        name = st.text_input(
            "Student name",
            placeholder="Enter your name",
            max_chars=40
        )
        submitted = st.form_submit_button("Enter NEUROMIND AI")

    if submitted:
        cleaned_name = " ".join(name.strip().split())
        if not cleaned_name:
            st.error("Please enter your name.")
        else:
            register_student(cleaned_name)
            st.session_state.username = cleaned_name
            st.session_state.notice = ""
            st.rerun()

    st.stop()

username = st.session_state.username
level = get_student_level(username)
history = load_history(username)
total_score = int(history["Score"].sum()) if not history.empty else 0
round_count = len(history)
accuracy = (
    100 * (history["Result"] == "Correct").sum() / round_count
    if round_count else 0
)

# ---------------- SIDEBAR ----------------
st.sidebar.title("🧠 NEUROMIND AI")
st.sidebar.caption("ADAPTIVE MEMORY LAB")
st.sidebar.success(f"Student: {username}")
st.sidebar.metric("Total Score", total_score)
st.sidebar.metric("Difficulty Level", level)

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "🏠 Dashboard",
        "🔢 Number Memory",
        "🟣 Pattern Memory",
        "📈 My Analytics",
        "🏆 Leaderboard"
    ]
)

if st.sidebar.button("Log Out"):
    st.session_state.username = ""
    st.session_state.number_target = None
    st.session_state.pattern_target = None
    st.session_state.notice = ""
    st.rerun()

# ---------------- HEADER ----------------
st.title("🧠 NEUROMIND AI")
st.caption("ADAPTIVE MEMORY CHALLENGE • STUDENT PERFORMANCE LAB")
st.markdown("---")

# ---------------- DASHBOARD ----------------
if page == "🏠 Dashboard":
    st.subheader(f"Welcome back, {username} 👋")
    st.write("Small challenges. Consistent practice. Measurable progress.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Score", total_score)
    c2.metric("Rounds Played", round_count)
    c3.metric("Accuracy", f"{accuracy:.1f}%")
    c4.metric("Current Level", level)

    st.markdown("### ✨ Choose your challenge")

    a, b = st.columns(2)
    with a:
        st.markdown("#### 🔢 Number Memory")
        st.write("Memorise a number sequence and recall it.")
        if st.button("Play Number Memory", use_container_width=True):
            st.session_state.number_target = None
            st.session_state.number_visible = False
            st.session_state.number_attempt += 1
            st.session_state.page_request = "🔢 Number Memory"
            st.rerun()

    with b:
        st.markdown("#### 🟣 Pattern Memory")
        st.write("Memorise a sequence of coloured symbols.")
        if st.button("Play Pattern Memory", use_container_width=True):
            st.session_state.pattern_target = None
            st.session_state.pattern_visible = False
            st.session_state.pattern_attempt += 1
            st.session_state.page_request = "🟣 Pattern Memory"
            st.rerun()

    if "page_request" in st.session_state:
        st.info(
            "Choose the requested challenge from the sidebar: "
            + st.session_state.page_request
        )

    st.markdown("### 💡 Practice suggestion")
    if round_count == 0:
        st.write("Play your first round to begin tracking your progress.")
    elif accuracy < 60:
        st.write("Try shorter practice sessions and focus on remembering the sequence carefully.")
    elif accuracy < 85:
        st.write("Good progress! Keep practising and aim for consistent accuracy.")
    else:
        st.write("Great consistency! Challenge yourself with the next difficulty level.")

# ---------------- NUMBER MEMORY ----------------
elif page == "🔢 Number Memory":
    st.subheader("🔢 Number Memory Challenge")
    st.write(f"Current difficulty: **Level {level}**")
    st.write("Memorise the number, hide it, then type it from memory.")

    if st.session_state.number_target is None:
        if st.button("Generate Number", use_container_width=True):
            digits = min(3 + level, 10)
            st.session_state.number_target = "".join(
                random.choices("0123456789", k=digits)
            )
            st.session_state.number_visible = True
            st.session_state.number_attempt += 1
            st.rerun()

    if st.session_state.number_target is not None:
        if st.session_state.number_visible:
            st.info("Memorise this number sequence.")
            st.markdown(
                "<div style='text-align:center; padding:30px;"
                "background:rgba(147,51,234,.18);border-radius:18px;"
                "font-size:42px;font-weight:bold;letter-spacing:8px;'>"
                + st.session_state.number_target +
                "</div>",
                unsafe_allow_html=True
            )
            if st.button("Hide Number"):
                st.session_state.number_visible = False
                st.rerun()
        else:
            answer = st.text_input(
                "Enter the number you remember",
                key=f"number_answer_{st.session_state.number_attempt}"
            )
            if st.button("Check Number"):
                if not answer.strip():
                    st.warning("Enter your answer first.")
                else:
                    old_level = get_student_level(username)
                    correct = answer.strip() == st.session_state.number_target
                    points = 10 * old_level if correct else 0
                    new_level = min(10, old_level + 1) if correct else max(1, old_level - 1)

                    save_round(username, "Number Memory", correct, points, old_level)
                    update_student_level(username, new_level)

                    st.session_state.number_target = None
                    st.session_state.number_visible = False

                    if correct:
                        st.session_state.notice = f"Correct! You earned {points} points."
                    else:
                        st.session_state.notice = "Not quite. Review the sequence and try again."
                    st.rerun()

    if st.session_state.notice:
        st.info(st.session_state.notice)

# ---------------- PATTERN MEMORY ----------------
elif page == "🟣 Pattern Memory":
    st.subheader("🟣 Pattern Memory Challenge")
    st.write(f"Current difficulty: **Level {level}**")
    st.write("Remember the symbols in order. Hide them and type the same sequence.")

    symbols = ["🔴", "🔵", "🟢", "🟡", "🟣", "🟠"]

    if st.session_state.pattern_target is None:
        if st.button("Create Pattern", use_container_width=True):
            length = min(2 + level, 8)
            st.session_state.pattern_target = random.choices(
                symbols, k=length
            )
            st.session_state.pattern_visible = True
            st.session_state.pattern_attempt += 1
            st.rerun()

    if st.session_state.pattern_target is not None:
        if st.session_state.pattern_visible:
            st.info("Memorise the order of these symbols.")
            st.markdown(
                "<div style='text-align:center;padding:28px;"
                "background:rgba(147,51,234,.18);border-radius:18px;"
                "font-size:38px;letter-spacing:8px;'>"
                + " ".join(st.session_state.pattern_target) +
                "</div>",
                unsafe_allow_html=True
            )
            if st.button("Hide Pattern"):
                st.session_state.pattern_visible = False
                st.rerun()
        else:
            st.write("Enter the symbols in the same order, separated by spaces.")
            st.caption("Example: 🔴 🔵 🟢")
            answer = st.text_input(
                "Your sequence",
                key=f"pattern_answer_{st.session_state.pattern_attempt}"
            )
            if st.button("Check Pattern"):
                if not answer.strip():
                    st.warning("Enter your sequence first.")
                else:
                    
                    symbol_map = {
                        "red": "🔴", "🔴": "🔴",
                        "blue": "🔵", "🔵": "🔵",
                        "green": "🟢", "🟢": "🟢",
                        "yellow": "🟡", "🟡": "🟡",
                        "purple": "🟣", "🟣": "🟣",
                        "orange": "🟠", "🟠": "🟠"
                    }

                    submitted_symbols = [
                        symbol_map.get(item.strip().lower(), item.strip())
                        for item in answer.split()
                    ]
                    old_level = get_student_level(username)
                    correct = submitted_symbols == st.session_state.pattern_target
                    points = 10 * old_level if correct else 0
                    new_level = min(10, old_level + 1) if correct else max(1, old_level - 1)

                    save_round(username, "Pattern Memory", correct, points, old_level)
                    update_student_level(username, new_level)

                    st.session_state.pattern_target = None
                    st.session_state.pattern_visible = False

                    if correct:
                        st.session_state.notice = f"Correct! You earned {points} points."
                    else:
                        st.session_state.notice = "Pattern incorrect. Try another round!"
                    st.rerun()



    if st.session_state.notice:
        st.info(st.session_state.notice)

# ---------------- ANALYTICS ----------------
elif page == "📈 My Analytics":
    st.subheader("📈 Your Performance Analytics")
    history = load_history(username)

    if history.empty:
        st.info("No rounds recorded yet. Play a challenge to see your analytics.")
    else:
        total_score = int(history["Score"].sum())
        rounds = len(history)
        accuracy = 100 * (history["Result"] == "Correct").sum() / rounds

        a, b, c = st.columns(3)
        a.metric("Total Score", total_score)
        b.metric("Rounds Played", rounds)
        c.metric("Accuracy", f"{accuracy:.1f}%")

        chart = px.bar(
            history.sort_values("Time"),
            x="Time",
            y="Score",
            color="Challenge",
            title="Score by Round",
            template="plotly_dark"
        )
        st.plotly_chart(chart, use_container_width=True)

        result_counts = history["Result"].value_counts().reset_index()
        result_counts.columns = ["Result", "Rounds"]
        pie = px.pie(
            result_counts,
            names="Result",
            values="Rounds",
            title="Correct vs Incorrect",
            template="plotly_dark"
        )
        st.plotly_chart(pie, use_container_width=True)

        st.markdown("### Recent rounds")
        st.dataframe(history, use_container_width=True, hide_index=True)

        if accuracy < 60:
            st.warning("Suggestion: practise short sequences and focus on accuracy.")
        elif accuracy < 85:
            st.info("Suggestion: continue practising and build consistency.")
        else:
            st.success("Suggestion: excellent game accuracy! Try harder levels.")

# ---------------- LEADERBOARD ----------------
elif page == "🏆 Leaderboard":
    st.subheader("🏆 Student Leaderboard")
    st.write("Rankings are based on accumulated points from completed rounds.")

    leaderboard = load_history()

    if leaderboard.empty:
        st.info("No scores yet. Complete a challenge to appear on the leaderboard.")
    else:
        leaderboard.insert(
            0, "Rank", range(1, len(leaderboard) + 1)
        )
        st.dataframe(
            leaderboard,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Scores are stored locally in SQLite. "
            "This leaderboard includes students who have played on this installation."
        )

st.markdown("---")
st.caption(
    "NEUROMIND AI • Student Project • Educational memory games, "
    "not a medical or intelligence assessment."
)
