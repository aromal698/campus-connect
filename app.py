from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import sqlite3
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import streamlit as st


# CampusConnect MVP. The SQLite file works for local testing and small demos.
# Streamlit Community Cloud does not guarantee that local files will persist;
# use a hosted database and real sign-in before relying on this for a campus.
APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "campusconnect.db"
try:
    INDIA_TZ = ZoneInfo("Asia/Kolkata")
except ZoneInfoNotFoundError:  # Windows may not ship the IANA time-zone database.
    INDIA_TZ = timezone(timedelta(hours=5, minutes=30))
DEPARTMENTS = ["CSE", "IT", "ECE", "EEE", "Mechanical", "Civil", "Chemical", "Biotechnology", "Other"]
SEMESTERS = list(range(1, 9))

st.set_page_config(
    page_title="CampusConnect | Student community",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def now_text():
    return datetime.now(INDIA_TZ).isoformat(timespec="seconds")


def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = connect_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                semester INTEGER,
                description TEXT NOT NULL DEFAULT '',
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memberships (
                group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                PRIMARY KEY (group_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS campus_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK (kind IN ('Activity', 'Notice')),
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                event_date TEXT NOT NULL,
                audience TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                important INTEGER NOT NULL DEFAULT 0,
                special INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
        if count == 0:
            for department in DEPARTMENTS:
                for semester in SEMESTERS:
                    conn.execute(
                        "INSERT INTO groups (name, department, semester, description, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            f"{department} · Semester {semester}",
                            department,
                            semester,
                            f"Study and class discussion for {department}, semester {semester}.",
                            "CampusConnect",
                            now_text(),
                        ),
                    )
        conn.commit()
    finally:
        conn.close()


def fetch_all(sql, params=()):
    conn = connect_db()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=()):
    conn = connect_db()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def execute(sql, params=()):
    conn = connect_db()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


def membership_exists(group_id, user_id):
    return fetch_one(
        "SELECT 1 FROM memberships WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    ) is not None


def open_group_chat(group_id):
    st.session_state.active_group_id = group_id
    st.session_state.page = "Group Chat"


def join_group(group_id):
    user_id = st.session_state.get("campus_user_id")
    name = st.session_state.get("display_name", "").strip()
    if user_id and name:
        execute(
            "INSERT OR IGNORE INTO memberships (group_id, user_id, display_name, joined_at) VALUES (?, ?, ?, ?)",
            (group_id, user_id, name, now_text()),
        )
        open_group_chat(group_id)


def member_groups(user_id):
    return fetch_all(
        """SELECT g.*, (SELECT COUNT(*) FROM memberships m WHERE m.group_id = g.id) AS member_count
           FROM groups g JOIN memberships mine ON mine.group_id = g.id
           WHERE mine.user_id = ? ORDER BY g.department, g.semester, g.name""",
        (user_id,),
    )


def all_groups():
    return fetch_all(
        """SELECT g.*, (SELECT COUNT(*) FROM memberships m WHERE m.group_id = g.id) AS member_count
           FROM groups g ORDER BY g.department, g.semester, g.name"""
    )


def post_rows(kind=None, only_today=False, today_value=None, important_first=False):
    conditions, params = [], []
    if kind:
        conditions.append("kind = ?")
        params.append(kind)
    if only_today:
        conditions.append("event_date = ?")
        params.append(today_value)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    order = "important DESC, event_date ASC, id DESC" if important_first else "event_date ASC, id DESC"
    return fetch_all(f"SELECT * FROM campus_posts {where} ORDER BY {order}", params)


def draft_with_gemini(kind, title, event_day, audience, creator_notes):
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        return (
            f"{title}\n\nDate: {event_day}\nFor: {audience}\n\n"
            f"{creator_notes or 'Add the location, time, registration details, and a contact person before publishing.'}"
        ), False
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=get_secret("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            contents=(
                f"Draft a concise campus {kind.lower()} for B.Tech students. "
                "Use only the facts supplied; do not invent venue, time, fees, registration links, or organizers. "
                "If information is missing, add a short [creator: add details] reminder. Return only the draft text.\n"
                f"Title: {title}\nDate: {event_day}\nAudience: {audience}\nCreator notes: {creator_notes or 'None'}"
            ),
        )
        return response.text or "Gemini returned an empty draft. Please write the details manually.", True
    except Exception:
        return "Gemini couldn't create a draft. Please write the details manually and check the API key/model settings.", False


def show_post(post):
    with st.container(border=True):
        flags = []
        if post["important"]:
            flags.append("📌 Important")
        if post["special"]:
            flags.append("✨ Today's special")
        st.caption(" · ".join([post["kind"], post["event_date"], post["audience"], *flags]))
        st.subheader(post["title"])
        st.write(post["body"])
        st.caption(f"Posted by {post['created_by']}")


def display_datetime(value):
    try:
        return datetime.fromisoformat(value).strftime("%d %b · %I:%M %p")
    except (TypeError, ValueError):
        return value


init_db()
st.session_state.setdefault("campus_user_id", os.urandom(12).hex())
st.session_state.setdefault("display_name", "")
st.session_state.setdefault("active_group_id", None)
today = datetime.now(INDIA_TZ).date()
today_iso = today.isoformat()

with st.sidebar:
    st.markdown("# 🎓 CampusConnect")
    st.caption("One campus. Every department.")
    display_name = st.text_input("Your display name", key="display_name", placeholder="e.g. Anu")
    department = st.selectbox("Your department", DEPARTMENTS, key="profile_department")
    semester = st.selectbox("Your semester", SEMESTERS, key="profile_semester")
    st.divider()
    page = st.radio(
        "Navigate",
        ["Home", "Study Groups", "Group Chat", "Campus Activities", "Notices", "Create Notice / Activity", "AI Study Buddy", "Feedback"],
        key="page",
        label_visibility="collapsed",
    )
    st.caption("Use a nickname here. This starter app does not verify student identity.")

st.markdown("<div class='eyebrow'>B.TECH STUDENT COMMUNITY</div>", unsafe_allow_html=True)
st.title(page)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1,h2,h3 { font-family: 'Manrope', sans-serif; letter-spacing: -0.03em; color:#173d32; }
    .eyebrow { color:#176b5b; font-size:.72rem; font-weight:700; letter-spacing:.16em; margin-bottom:.45rem; }
    .hero { padding:1.8rem 2rem; border-radius:22px; background:linear-gradient(120deg,#e3f1e8,#f2f6ee 70%,#e8f2ed); border:1px solid #d2e3d8; }
    .hero h2 { margin:0 0 .5rem; color:#153b33; font-size:2rem; }
    .hero p { color:#334e47; margin:0; line-height:1.65; max-width:760px; }
    .date-card { background:#edf5ef; border-left:5px solid #176b5b; padding:1rem 1.25rem; border-radius:12px; }
    [data-testid="stSidebar"] { background:#edf3ef; }
    div.stButton > button { border-radius:12px; border-color:#176b5b; color:#14584c; font-weight:600; }
    div.stButton > button:hover { background:#e5f2ec; border-color:#14584c; color:#103f36; }
    div.stButton > button:focus-visible { outline:3px solid #176b5b; outline-offset:2px; }
    [data-testid="stMetric"] { background:#fff; border:1px solid #dbe5df; padding:1rem; border-radius:16px; }
    </style>
    """,
    unsafe_allow_html=True,
)

if not display_name.strip():
    st.warning("Add a display name in the left sidebar to join groups, chat, and post campus updates.")

if page == "Home":
    st.markdown(
        "<div class='hero'><h2>Good ideas grow across departments.</h2><p>Find a study group, join its chat, or keep up with today's campus activities and notices. Choose a page from the menu to get started.</p></div>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        f"<div class='date-card'><b>Today · {today.strftime('%A, %d %B %Y')}</b><br>Campus special: check today's highlighted event below, or see notices for important updates.</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    activities_today = post_rows(kind="Activity", only_today=True, today_value=today_iso)
    special_today = fetch_all(
        "SELECT * FROM campus_posts WHERE event_date = ? AND special = 1 ORDER BY id DESC",
        (today_iso,),
    )
    important_notices = fetch_all(
        "SELECT * FROM campus_posts WHERE kind = 'Notice' AND important = 1 ORDER BY id DESC LIMIT 5"
    )
    latest_notices = fetch_all(
        "SELECT * FROM campus_posts WHERE kind = 'Notice' ORDER BY important DESC, id DESC LIMIT 5"
    )
    memberships_count = fetch_one("SELECT COUNT(*) FROM memberships WHERE user_id = ?", (st.session_state.campus_user_id,))[0]
    groups_count = fetch_one("SELECT COUNT(*) FROM groups")[0]
    metric_cols = st.columns(3)
    metric_cols[0].metric("Groups to explore", groups_count)
    metric_cols[1].metric("Your groups", memberships_count)
    metric_cols[2].metric("Activities today", len(activities_today))

    left, right = st.columns([1.1, 0.9])
    with left:
        st.subheader("📅 Today's campus activities")
        if activities_today:
            for post in activities_today:
                show_post(post)
        else:
            st.info("No activities are posted for today yet. Check Campus Activities for upcoming events.")
        st.subheader("✨ Today's special")
        if special_today:
            for post in special_today:
                show_post(post)
        else:
            st.write("No special campus event has been highlighted for today.")
    with right:
        st.subheader("📌 Important messages")
        if important_notices:
            for post in important_notices:
                show_post(post)
        else:
            st.info("There are no pinned important notices yet.")
        st.subheader("📰 Latest notices")
        if latest_notices:
            for post in latest_notices:
                show_post(post)
        else:
            st.info("New notices will appear here when a campus creator publishes them.")

    st.caption(
        "Prototype note: this app uses a local SQLite file and simple display names. Streamlit Community Cloud can delete local files; use a hosted database and verified sign-in before relying on it for permanent student records."
    )

elif page == "Study Groups":
    st.caption("A starter group is ready for every department and semester. Join one to unlock its group chat, or create your own.")
    tab_my, tab_browse, tab_create = st.tabs(["My groups", "Browse groups", "Create a group"])
    with tab_my:
        joined = member_groups(st.session_state.campus_user_id)
        if not joined:
            st.info("You haven't joined a group yet. Browse the groups to find your department and semester.")
        for group in joined:
            with st.container(border=True):
                st.subheader(group["name"])
                st.write(group["description"] or "Student group")
                st.caption(f"{group['member_count']} members · Created by {group['created_by']}")
                st.button(
                    "Open group chat",
                    key=f"mychat_{group['id']}",
                    type="primary",
                    on_click=open_group_chat,
                    args=(group["id"],),
                )
    with tab_browse:
        filter_col1, filter_col2 = st.columns(2)
        filter_department = filter_col1.selectbox("Filter department", ["All departments", *DEPARTMENTS], key="filter_department")
        filter_semester = filter_col2.selectbox("Filter semester", ["All semesters", *SEMESTERS], key="filter_semester")
        groups = all_groups()
        if filter_department != "All departments":
            groups = [g for g in groups if g["department"] == filter_department]
        if filter_semester != "All semesters":
            groups = [g for g in groups if g["semester"] == filter_semester]
        for group in groups:
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1.2])
                with col_info:
                    st.subheader(group["name"])
                    st.write(group["description"] or "Student-created group")
                    st.caption(f"{group['member_count']} members · Created by {group['created_by']}")
                with col_action:
                    is_member = membership_exists(group["id"], st.session_state.campus_user_id)
                    if is_member:
                        st.button(
                            "Open chat",
                            key=f"open_{group['id']}",
                            type="primary",
                            on_click=open_group_chat,
                            args=(group["id"],),
                        )
                    else:
                        st.button(
                            "Join group",
                            key=f"join_{group['id']}",
                            disabled=not display_name.strip(),
                            on_click=join_group,
                            args=(group["id"],),
                        )
    with tab_create:
        with st.form("create_group_form", clear_on_submit=True):
            new_group_name = st.text_input("Group name", placeholder="e.g. Robotics project team")
            new_group_description = st.text_area("What is this group for?", placeholder="Subjects, project goals, meeting plans...")
            group_col1, group_col2 = st.columns(2)
            new_group_department = group_col1.selectbox("Department", ["Cross-department", *DEPARTMENTS], key="new_group_department")
            new_group_semester = group_col2.selectbox("Semester", ["Any semester", *SEMESTERS], key="new_group_semester")
            create_group = st.form_submit_button("Create group", type="primary", disabled=not display_name.strip())
        if create_group:
            group_id = execute(
                "INSERT INTO groups (name, department, semester, description, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    new_group_name.strip(),
                    new_group_department,
                    None if new_group_semester == "Any semester" else new_group_semester,
                    new_group_description.strip(),
                    display_name.strip(),
                    now_text(),
                ),
            ) if new_group_name.strip() else None
            if group_id:
                execute(
                    "INSERT OR IGNORE INTO memberships (group_id, user_id, display_name, joined_at) VALUES (?, ?, ?, ?)",
                    (group_id, st.session_state.campus_user_id, display_name.strip(), now_text()),
                )
                st.success("Group created and joined. Open it under My groups to start chatting.")
                st.rerun()
            else:
                st.warning("Please add a name for your group.")

elif page == "Group Chat":
    joined = member_groups(st.session_state.campus_user_id)
    if not joined:
        st.info("Join a study group first. Then its chat will appear here.")
        if st.button("Browse study groups"):
            st.session_state.page = "Study Groups"
            st.rerun()
    else:
        group_by_id = {g["id"]: g for g in joined}
        joined_ids = list(group_by_id)
        default_index = joined_ids.index(st.session_state.active_group_id) if st.session_state.active_group_id in joined_ids else 0
        selected_group_id = st.selectbox(
            "Choose a group chat",
            joined_ids,
            index=default_index,
            format_func=lambda group_id: group_by_id[group_id]["name"],
        )
        st.session_state.active_group_id = selected_group_id
        selected_group = group_by_id[selected_group_id]
        st.caption(f"{selected_group['member_count']} members · Messages are visible to members of this group.")
        messages = fetch_all(
            """SELECT * FROM (SELECT * FROM messages WHERE group_id = ? ORDER BY id DESC LIMIT 100)
               ORDER BY id ASC""",
            (selected_group_id,),
        )
        for message in messages:
            role = "user" if message["user_id"] == st.session_state.campus_user_id else "assistant"
            with st.chat_message(role, avatar="🙂" if role == "user" else "💬"):
                st.markdown(f"**{message['display_name']}** · {display_datetime(message['created_at'])}")
                st.write(message["message"])
        new_message = st.chat_input("Write a message to your group...", key=f"group_message_{selected_group_id}")
        if new_message:
            if not display_name.strip():
                st.warning("Add your display name in the sidebar before chatting.")
            elif len(new_message) > 2000:
                st.warning("Keep messages under 2,000 characters.")
            else:
                execute(
                    "INSERT INTO messages (group_id, user_id, display_name, message, created_at) VALUES (?, ?, ?, ?, ?)",
                    (selected_group_id, st.session_state.campus_user_id, display_name.strip(), new_message.strip(), now_text()),
                )
                st.rerun()

elif page in ("Campus Activities", "Notices"):
    kind = "Activity" if page == "Campus Activities" else "Notice"
    st.caption("Campus updates are drafted by their creator and published to the front page.")
    posts = post_rows(kind=kind, important_first=(kind == "Notice"))
    if not posts:
        st.info(f"No {kind.lower()} posts yet. Check back later.")
    for post in posts:
        show_post(post)

elif page == "Create Notice / Activity":
    st.caption("Enter the facts, ask Gemini for an editable draft, review it, then publish. AI drafts are never published automatically.")
    st.caption("Do not include personal student details in AI draft notes. Verify every date, venue, time, and link before publishing.")
    if not get_secret("GEMINI_API_KEY"):
        st.info("Gemini is not configured. You can still write and publish a post manually; AI drafting will work after you add GEMINI_API_KEY in Streamlit Secrets.")
    with st.container(border=True):
        new_kind = st.selectbox("What are you creating?", ["Activity", "Notice"], key="post_kind")
        new_title = st.text_input("Title", key="post_title", placeholder="e.g. Department project expo")
        event_date = st.date_input("Date", value=today, key="post_date")
        audience = st.selectbox("Audience", ["All departments", *DEPARTMENTS], key="post_audience")
        creator_notes = st.text_input("Key facts for the AI draft (optional)", placeholder="Time, venue, registration, contact person", key="creator_notes")
        if st.button("✨ Draft details with Gemini", disabled=not new_title.strip()):
            draft, used_ai = draft_with_gemini(
                new_kind,
                new_title.strip(),
                event_date.strftime("%A, %d %B %Y"),
                audience,
                creator_notes.strip(),
            )
            st.session_state["post_body"] = draft
            if used_ai:
                st.success("Gemini drafted the post. Review and edit it below before publishing.")
            else:
                st.info("Added an editable starter draft. Connect Gemini for an AI-written draft.")
        body = st.text_area(
            "Review and edit the post details",
            key="post_body",
            height=180,
            placeholder="Include only confirmed information, such as time, location, sign-up steps, and contact details.",
        )
        check_col1, check_col2 = st.columns(2)
        important = check_col1.checkbox("Pin this as an important notice", disabled=(new_kind != "Notice"), key="post_important")
        special = check_col2.checkbox("Highlight this as today's special", disabled=(new_kind != "Activity" or event_date != today), key="post_special")
        publish = st.button("Publish to campus", type="primary", disabled=not display_name.strip())
        if publish:
            if not new_title.strip() or not body.strip():
                st.warning("Add a title and review the post details before publishing.")
            else:
                execute(
                    "INSERT INTO campus_posts (kind, title, body, event_date, audience, created_by, created_at, important, special) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        new_kind,
                        new_title.strip(),
                        body.strip(),
                        event_date.isoformat(),
                        audience,
                        display_name.strip(),
                        now_text(),
                        int(important and new_kind == "Notice"),
                        int(special and event_date == today and new_kind == "Activity"),
                    ),
                )
                st.success(f"{new_kind} published. It will appear on the home page and in {new_kind.lower()}s.")
                st.rerun()

elif page == "AI Study Buddy":
    st.caption("Ask for a concept explanation, study plan, or hints. Check important course details with your faculty.")
    if not get_secret("GEMINI_API_KEY"):
        st.info("Gemini isn't connected yet. Add GEMINI_API_KEY to Streamlit Secrets to turn on the study buddy.")
    st.warning("Privacy: Free-tier Gemini prompts may be used to improve Google's products. Don't enter your name, contact details, private student information, or confidential material.")
    for message in st.session_state.setdefault("study_chat", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Ask something you are learning...")
    if question:
        study_chat = st.session_state.study_chat
        study_chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking through it..."):
                answer = None
                if get_secret("GEMINI_API_KEY"):
                    history = "\n".join(f"{m['role']}: {m['content']}" for m in study_chat[:-1][-8:])
                    try:
                        from google import genai
                        from google.genai import types

                        client = genai.Client(api_key=get_secret("GEMINI_API_KEY"))
                        response = client.models.generate_content(
                            model=get_secret("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                            config=types.GenerateContentConfig(
                                system_instruction=(
                                    "You are CampusConnect's friendly study buddy for B.Tech students across departments. "
                                    f"The student's profile is {department}, semester {semester}. Explain step by step, "
                                    "give hints for assignments rather than dishonest submissions, and say when you are unsure."
                                )
                            ),
                            contents=f"Recent conversation:\n{history}\nuser: {question}",
                        )
                        answer = response.text
                    except Exception:
                        answer = "Gemini could not answer just now. Check the Gemini API key, model, and usage limits in Google AI Studio."
                if not answer:
                    answer = "Demo mode: connect Gemini by adding GEMINI_API_KEY in Streamlit Secrets."
                st.markdown(answer)
        study_chat.append({"role": "assistant", "content": answer})

elif page == "Feedback":
    st.caption("Tell us what works, what is confusing, and what would help your campus community.")
    with st.form("feedback_form", clear_on_submit=True):
        category = st.selectbox("Feedback topic", ["App idea", "Bug or problem", "Study groups", "Campus notice/activity", "Accessibility", "Other"])
        feedback_text = st.text_area("Your feedback", max_chars=2000, placeholder="Share your suggestion or describe the problem...")
        send_feedback = st.form_submit_button("Send feedback", type="primary", disabled=not display_name.strip())
    if send_feedback:
        if feedback_text.strip():
            execute(
                "INSERT INTO feedback (display_name, category, message, created_at) VALUES (?, ?, ?, ?)",
                (display_name.strip(), category, feedback_text.strip(), now_text()),
            )
            st.success("Thanks! Your feedback has been recorded.")
        else:
            st.warning("Write a short message before sending feedback.")
