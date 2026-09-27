import os
from datetime import date

import streamlit as st


st.set_page_config(
    page_title="CampusConnect | B.Tech community",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


DEMO_POSTS = [
    {"name": "Aarav · CSE · 3rd year", "tag": "Project", "title": "Looking for an ECE teammate for a smart energy meter", "body": "I’m building a dashboard and need someone interested in sensors or embedded systems. Beginners welcome!", "likes": 12},
    {"name": "Meera · Mechanical · 2nd year", "tag": "Study help", "title": "Thermodynamics study circle this Friday", "body": "Let’s solve previous exam questions together in the library. Bring one question you found difficult.", "likes": 8},
    {"name": "Student Innovation Cell", "tag": "Opportunity", "title": "Campus mini-hackathon registrations are open", "body": "Form a team of 2–4 students from any department. Share a useful campus idea and build a small prototype.", "likes": 24},
]

DEFAULT_GROUPS = [
    {"name": "First Year Study Lounge", "department": "All departments", "members": 86, "topic": "Maths · Physics · Programming"},
    {"name": "Campus App Builders", "department": "Cross-department", "members": 34, "topic": "Projects · UI · APIs"},
    {"name": "Core Engineering Exam Prep", "department": "Mechanical + Civil", "members": 21, "topic": "Materials · Mechanics"},
]


def init_state():
    st.session_state.setdefault("posts", DEMO_POSTS.copy())
    st.session_state.setdefault("groups", DEFAULT_GROUPS.copy())
    st.session_state.setdefault("joined_groups", set())
    st.session_state.setdefault("chat", [])


def get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


def ask_ai(question, department, year):
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        history = st.session_state.chat[-8:]
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        response = client.responses.create(
            model=get_secret("OPENAI_MODEL", "gpt-5"),
            instructions=(
                "You are CampusConnect's friendly study buddy for B.Tech students across all departments. "
                f"The student is in {department}, year {year}. Explain concepts step by step in clear language. "
                "Offer hints and learning support, not dishonest exam or assignment completion. "
                "If a question depends on college-specific facts that you do not have, say so and suggest asking a student or faculty member."
            ),
            input=f"Recent conversation:\n{prompt}\nuser: {question}",
        )
        return response.output_text
    except Exception as exc:
        return f"I couldn't reach the AI service. Check the API key and model setting in Streamlit secrets. Details: {exc}"


init_state()

with st.sidebar:
    st.markdown("# 🎓 CampusConnect")
    st.caption("One campus. Every department.")
    page = st.radio("Go to", ["Home", "Campus feed", "Study groups", "Find teammates", "AI study buddy"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Your student profile**")
    department = st.selectbox("Department", ["CSE", "ECE", "EEE", "Mechanical", "Civil", "Chemical", "Other"])
    year = st.selectbox("Year", ["1st year", "2nd year", "3rd year", "4th year"])
    st.caption("Demo version: posts and groups reset when the app restarts.")

st.markdown("<div class='topline'>B.TECH STUDENT COMMUNITY</div>", unsafe_allow_html=True)
st.title(page)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Manrope', sans-serif; letter-spacing: -0.035em; }
.topline { color:#497267; font-size:0.72rem; font-weight:700; letter-spacing:.16em; margin:0 0 .5rem; }
.hero { padding:2rem 2.2rem; border-radius:22px; background:linear-gradient(120deg,#e9f4ec,#f4f1e7 70%,#f4e8d8); border:1px solid #e5e8dc; }
.hero h2 { margin:0 0 .6rem; font-size:2rem; color:#183a31; }
.hero p { color:#40564e; max-width:650px; margin:0; line-height:1.65; }
.tile { background:#fff; border:1px solid #e7ebe6; border-radius:18px; padding:1.15rem 1.3rem; min-height:125px; }
.tile b { color:#193b32; font-size:1rem; }
.tile p { color:#66746e; font-size:.9rem; margin:.45rem 0 0; }
[data-testid="stSidebar"] { background:#f5f6f1; }
div.stButton > button { border-radius:12px; }
</style>
""", unsafe_allow_html=True)

if page == "Home":
    st.markdown("<div class='hero'><h2>Good ideas grow across departments.</h2><p>Find your people, learn together, and turn class projects into real things. Start with a study group, share a campus opportunity, or ask your AI study buddy.</p></div>", unsafe_allow_html=True)
    st.write("")
    a, b, c = st.columns(3)
    for col, title, desc in [(a, "📚 Learn together", "Find peer notes, study groups, and explanations."), (b, "🧩 Build across branches", "Meet teammates whose skills complement yours."), (c, "🚀 Discover opportunities", "Keep up with events, internships, and challenges.")]:
        with col:
            st.markdown(f"<div class='tile'><b>{title}</b><p>{desc}</p></div>", unsafe_allow_html=True)
    st.write("")
    st.subheader("A few things happening")
    cols = st.columns(3)
    for col, (label, value) in zip(cols, [("Community posts", len(st.session_state.posts)), ("Study groups", len(st.session_state.groups)), ("Groups you joined", len(st.session_state.joined_groups))]):
        col.metric(label, value)
    st.info("Choose a section from the left to explore the prototype. Your department and year help personalize the AI study buddy.")

elif page == "Campus feed":
    st.caption("Questions, useful resources, project ideas, and opportunities shared by students.")
    with st.expander("＋ Share something with campus", expanded=True):
        with st.form("post_form", clear_on_submit=True):
            post_title = st.text_input("Title", placeholder="What would you like other students to know?")
            post_body = st.text_area("Details", placeholder="Add enough context for students from other departments too.")
            post_tag = st.selectbox("Post type", ["Question", "Resource", "Project", "Opportunity", "Study help"])
            submitted = st.form_submit_button("Publish post", type="primary")
            if submitted:
                if post_title.strip() and post_body.strip():
                    st.session_state.posts.insert(0, {"name": f"You · {department} · {year}", "tag": post_tag, "title": post_title.strip(), "body": post_body.strip(), "likes": 0})
                    st.success("Your post is now in the campus feed.")
                else:
                    st.warning("Add a title and details before publishing.")
    for i, post in enumerate(st.session_state.posts):
        with st.container(border=True):
            st.caption(f"{post['name']}  ·  {post['tag']}")
            st.subheader(post["title"])
            st.write(post["body"])
            if st.button(f"♡  Helpful · {post['likes']}", key=f"like_{i}"):
                post["likes"] += 1
                st.rerun()

elif page == "Study groups":
    st.caption("Join a focused study group or create a new one for your class, subject, or project.")
    with st.expander("Create a group"):
        with st.form("group_form", clear_on_submit=True):
            group_name = st.text_input("Group name")
            group_topic = st.text_input("Subjects or interests", placeholder="e.g. Data structures · placement prep")
            group_scope = st.selectbox("Who is it for?", ["All departments", department, "Cross-department"])
            made = st.form_submit_button("Create group", type="primary")
            if made:
                if group_name.strip():
                    st.session_state.groups.insert(0, {"name": group_name.strip(), "department": group_scope, "members": 1, "topic": group_topic or "Student-created group"})
                    st.success("Group created. Invite classmates to join!")
                else:
                    st.warning("Give your group a name first.")
    for idx, group in enumerate(st.session_state.groups):
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.subheader(group["name"])
                st.caption(f"{group['department']} · {group['members']} members")
                st.write(group["topic"])
            with right:
                if idx in st.session_state.joined_groups:
                    st.button("Joined ✓", key=f"join_{idx}", disabled=True)
                elif st.button("Join group", key=f"join_{idx}"):
                    st.session_state.joined_groups.add(idx)
                    group["members"] += 1
                    st.rerun()

elif page == "Find teammates":
    st.caption("Make interdisciplinary projects easier to start. Post a project and say which skills you need.")
    with st.form("team_form", clear_on_submit=True):
        project = st.text_input("Project idea", placeholder="e.g. Smart plant watering system")
        skills = st.text_input("Skills you have", placeholder="e.g. Python, CAD, electronics")
        looking = st.text_input("Skills you are looking for", placeholder="e.g. sensors, mobile design, presentation")
        if st.form_submit_button("Post teammate request", type="primary"):
            if project.strip():
                st.session_state.posts.insert(0, {"name": f"You · {department} · {year}", "tag": "Team finder", "title": project.strip(), "body": f"I can contribute: {skills or 'still learning'}. Looking for: {looking or 'open to collaborators'}.", "likes": 0})
                st.success("Added to the campus feed. Other students can find your project there.")
            else:
                st.warning("Add a short project idea first.")
    st.divider()
    st.subheader("Ideas to get you started")
    st.markdown("- A low-cost air-quality monitor: ECE + CSE + Civil\n- A campus navigation app: CSE + design-minded students from any branch\n- A small solar-powered charging station: EEE + Mechanical + CSE")
    st.caption("These are sample prompts. Replace them with projects and teams from your campus.")

elif page == "AI study buddy":
    st.caption("Ask for a concept explanation, a study plan, or hints for a problem. Verify important course details with your faculty.")
    if not get_secret("OPENAI_API_KEY"):
        st.info("The AI connection is optional and is not configured yet. Add your API key as a Streamlit secret when you are ready; setup steps are in README.md.")
    for message in st.session_state.chat:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if question := st.chat_input("Ask something you are learning…"):
        st.session_state.chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking through it…"):
                answer = ask_ai(question, department, year)
                if answer is None:
                    answer = "I’m in demo mode until an API key is configured. You can still explore the rest of CampusConnect, and the README explains how to connect the AI study buddy."
                st.markdown(answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})
