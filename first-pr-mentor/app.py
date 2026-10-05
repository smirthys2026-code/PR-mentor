"""First-PR Mentor - Streamlit UI (dashboard-style design)."""
import html
import itertools
import json
import math
import os
from pathlib import Path

import streamlit as st

import coach
import github_client as gh
import llm
import prompts

st.set_page_config(page_title="First-PR Mentor", page_icon="🌱", layout="wide")

DEMO = json.loads((Path(__file__).parent / "demo_data.json").read_text(encoding="utf-8"))
SAMPLE_URL = DEMO["issue"]["html_url"]  # fictional issue, always served from demo data
SKILLS = ["python", "javascript", "typescript", "java", "c++", "go", "rust", "html/css", "react"]

# ---------- Look and feel ----------
# All colours live in the :root block at the top. Change them there and the whole app updates.
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --accent: #16a34a;   /* green used for highlights */
  --ink: #111111;      /* near-black used for active tabs and primary buttons */
  --page: #dcdee6;     /* grey-lilac page background */
  --shell: #f4f4f4;    /* big rounded panel */
  --card: #ffffff;     /* small cards */
  --soft: #f6f6f6;     /* light grey inside cards */
  --muted: #6b7280;    /* grey text */
}

/* ---------- Page ---------- */
.stApp { background: var(--page); }
html, body, .stApp, .stApp button, .stApp input, .stApp label, .stApp p {
  font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}
#MainMenu, footer, [data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }

/* The big rounded panel that holds everything */
.block-container, div[data-testid="stMainBlockContainer"] {
  max-width: 1180px;
  margin: 16px auto;
  padding: 28px 32px 36px 32px !important;
  background: var(--shell);
  border-radius: 32px;
  box-shadow: 0 8px 30px rgba(17, 24, 39, 0.06);
}

/* ---------- Top bar ---------- */
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.brand { display: inline-flex; align-items: center; gap: 10px; background: var(--card); padding: 8px 18px 8px 10px;
         border-radius: 999px; font-weight: 700; font-size: 0.95rem; }
.brand .logo { background: var(--ink); border-radius: 50%; width: 32px; height: 32px; display: inline-flex;
               align-items: center; justify-content: center; font-size: 1rem; }
.topright { display: flex; align-items: center; gap: 10px; }
.tagline { background: var(--card); padding: 10px 18px; border-radius: 999px; color: var(--muted); font-size: 0.85rem; }

/* ---------- Tabs: pill buttons, active one is black ---------- */
[role="tablist"] { gap: 10px; justify-content: center; background: transparent; padding-bottom: 14px; border: none !important; box-shadow: none !important; }
[role="tab"], button[data-baseweb="tab"] {
  background: var(--card); border-radius: 999px; padding: 10px 24px; height: auto; border: none !important;
  transition: background .15s;
}
[role="tab"] p, button[data-baseweb="tab"] p { font-weight: 600; font-size: 0.92rem; margin: 0; color: var(--ink); }
[role="tab"]:hover { background: #e9eaee; }
[role="tab"][aria-selected="true"], button[data-baseweb="tab"][aria-selected="true"] { background: var(--ink); }
[role="tab"][aria-selected="true"] p, button[data-baseweb="tab"][aria-selected="true"] p { color: #fff; }
[role="tablist"]::after { display: none !important; }
.react-aria-SelectionIndicator, div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }

/* ---------- Headings ---------- */
.hero { font-size: 2.3rem; font-weight: 600; letter-spacing: -0.03em; line-height: 1.1; margin: 4px 0 16px 0; color: var(--ink); }
h3, h4 { letter-spacing: -0.02em; }
.card-title { font-size: 1.05rem; font-weight: 600; margin: 2px 0 10px 0; }

/* ---------- Cards: every container made with card() ---------- */
div[class*="st-key-card"] {
  background: var(--card); border-radius: 22px; padding: 18px 20px;
  box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04); transition: box-shadow .2s;
}
div[class*="st-key-card"]:hover { box-shadow: 0 8px 22px rgba(17, 24, 39, 0.08); }
div[class*="st-key-card"][class*="_done"] { background: #f0fdf4; box-shadow: inset 0 0 0 1.5px #86efac; }

div[data-testid="stExpander"] details { border: none; background: var(--soft); border-radius: 14px; }
div[data-testid="stAlert"] { border-radius: 16px; border: none; }
div[data-testid="stCodeBlock"], pre { border-radius: 14px; }

/* ---------- Inputs ---------- */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div,
div[data-testid="stTextInputRootElement"] {
  border-radius: 14px; background: var(--soft); border: 1px solid #e8eaee;
}
div[data-testid="stMultiSelect"] [data-baseweb="select"] > div, div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
div[data-testid="stMultiSelect"] div:has(> [data-testid="stMultiSelectTagsContainer"]) {
  background: var(--soft) !important; border: 1px solid #e8eaee !important; border-radius: 14px !important;
}
div[data-testid="stTextInputRootElement"]:focus-within, div[data-baseweb="select"] > div:focus-within { border-color: var(--accent); }
span[data-baseweb="tag"] { background: var(--ink); color: #fff; border-radius: 999px; }

/* ---------- Buttons: white pill by default, black pill for primary ---------- */
.stButton > button { border-radius: 999px; padding: 0.45rem 1.3rem; font-weight: 600; border: 1px solid #e5e7eb; background: #fff; color: var(--ink); transition: all .15s; }
.stButton > button:hover { border-color: var(--ink); color: var(--ink); }
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] { background: var(--ink); border-color: var(--ink); }
.stButton > button[kind="primary"] p, button[data-testid="stBaseButton-primary"] p { color: #fff; }
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover { background: var(--accent); border-color: var(--accent); }

a { color: #15803d !important; }
section[data-testid="stSidebar"] { background: #fff; }

/* ---------- Coloured status pills (GOOD / ATTENTION style) ---------- */
.pill { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: 0.72rem; font-weight: 700;
        letter-spacing: 0.04em; color: #fff; white-space: nowrap; }
.pill.green { background: #22c55e; }
.pill.yellow { background: #facc15; color: #111; }
.pill.orange { background: #f97316; }
.pill.black { background: var(--ink); }

/* ---------- Big number cards, like "87%" in the design ---------- */
.stat { background: var(--soft); border-radius: 18px; padding: 14px 18px; height: 100%; }
.stat.white { background: var(--card); }
.stat-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.stat-label { color: var(--muted); font-size: 0.85rem; font-weight: 500; }
.stat-num { font-size: 2.5rem; font-weight: 500; letter-spacing: -0.03em; line-height: 1.15; margin-top: 6px; }

/* ---------- Score list with dotted lines, like the "Overview" card ---------- */
.score-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 0.86rem; }
.score-row .n { color: var(--muted); width: 14px; text-align: center; font-size: 0.78rem; }
.score-row .dots { flex: 1; border-bottom: 1.5px dotted #d1d5db; transform: translateY(3px); }
.chip { padding: 2px 9px; border-radius: 8px; font-weight: 700; font-size: 0.75rem; color: #fff; }
.chip.green { background: #22c55e; }
.chip.yellow { background: #facc15; color: #111; }
.chip.orange { background: #f97316; }

/* ---------- Green promo card, like "Upgrade your plan" ---------- */
.promo { background: linear-gradient(135deg, #15803d, #22c55e); border-radius: 22px; padding: 22px 24px; color: #fff; height: 100%; }
.promo h3 { color: #fff; font-size: 1.7rem; font-weight: 600; margin: 0 0 6px 0; line-height: 1.1; padding: 0; }
.promo p { margin: 0; opacity: 0.92; font-size: 0.92rem; }
.promo.tall { min-height: 205px; display: flex; flex-direction: column; justify-content: space-between; gap: 14px; }
.promo-chip { display: inline-block; align-self: flex-start; background: #fff; color: var(--ink); font-weight: 600;
              font-size: 0.8rem; padding: 7px 16px; border-radius: 999px; }

/* ---------- Progress card: ring + striped bar, like "Passing rate" ---------- */
.progress-card { background: var(--card); border-radius: 22px; padding: 18px 22px; margin-bottom: 12px;
                 display: flex; align-items: center; gap: 22px; }
.progress-card .main { flex: 1; min-width: 0; }
.bar { height: 36px; border-radius: 14px; margin-top: 10px; overflow: hidden;
       background: repeating-linear-gradient(135deg, #e5e7eb 0 6px, #f3f4f6 6px 12px); }
.bar > span { display: block; height: 100%; background: var(--accent); border-radius: 14px; transition: width .4s; }

/* ---------- Small screens ---------- */
@media (max-width: 760px) {
  .block-container, div[data-testid="stMainBlockContainer"] { padding: 18px 14px 24px 14px !important; border-radius: 22px; margin: 6px auto; }
  .hero { font-size: 1.7rem; }
  .tagline { display: none; }
  .progress-card { flex-direction: column; align-items: flex-start; }
}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

# ---------- Sidebar ----------
demo_mode = st.sidebar.checkbox("Demo mode", help="Uses saved sample data. Makes zero network calls.")
if demo_mode:
    st.sidebar.info("Demo mode is on: showing saved sample data.")
else:
    # Only shows whether settings exist, never their values
    st.sidebar.caption(f"GitHub token: {'✅ set' if os.getenv('GITHUB_TOKEN') else '⚠️ missing (low rate limit)'}")
    st.sidebar.caption(f"AI model: {'✅ set' if os.getenv('LLM_BASE_URL') and os.getenv('LLM_MODEL') else '⚠️ missing (see .env.example)'}")

st.session_state.setdefault("issue_url", "")

# Top bar (drawn after the sidebar, because it needs to know if Demo mode is on)
mode_pill = '<span class="pill green">DEMO MODE</span>' if demo_mode else '<span class="pill black">LIVE</span>'
st.markdown(
    '<div class="topbar">'
    '<div class="brand"><span class="logo">🌱</span> First-PR Mentor</div>'
    '<div class="topright"><div class="tagline">From \'I want to contribute\' to your first PR</div>' + mode_pill + '</div>'
    '</div>',
    unsafe_allow_html=True,
)


# ---------- Small helpers ----------
def esc(text):
    """Escape characters that would break Streamlit markdown."""
    return str(text).replace("[", "\\[").replace("]", "\\]").replace("$", "\\$")


def num(value, default=0):
    try:
        return max(0, min(10, int(value)))
    except (TypeError, ValueError):
        return default


def minutes(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return "?"


def age_text(days):
    if days < 1:
        return "today"
    return f"{days} days ago" if days < 30 else f"{days // 30} mo ago"


def use_issue(url):  # button callback: runs before the page reruns, so it can set the input's value
    st.session_state["issue_url"] = url
    st.session_state["selected_notice"] = True


def fill_example():
    st.session_state["issue_url"] = SAMPLE_URL


# ----- New helpers for the dashboard look -----
def pill(text, level="green"):
    """Small coloured label. level is green, yellow, orange or black."""
    return f'<span class="pill {level}">{html.escape(str(text))}</span>'


def level_for(value, good, ok):
    """Higher is better: green if value >= good, yellow if value >= ok, else orange."""
    return "green" if value >= good else "yellow" if value >= ok else "orange"


_card_ids = itertools.count()  # restarts at 0 on every rerun, so keys stay unique and stable


def card(done=False):
    """A white rounded card. The key gives the container a CSS class (st-key-card_N) that the STYLE block targets."""
    return st.container(key=f"card_{next(_card_ids)}" + ("_done" if done else ""))


def stat(label, value, pill_html, plain=False):
    """A big-number card: small label + pill on top, large value below."""
    cls = "stat white" if plain else "stat"
    return (f'<div class="{cls}"><div class="stat-top"><span class="stat-label">{html.escape(label)}</span>{pill_html}</div>'
            f'<div class="stat-num">{html.escape(str(value))}</div></div>')


def radar_svg(values):
    """Radar chart. values = list of numbers from 0 to 10. Returns an SVG string."""
    n, cx, cy, radius = len(values), 120, 120, 78

    def point(i, r):  # position of spoke i at distance r from the centre
        angle = -math.pi / 2 + 2 * math.pi * i / n
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    def poly(r_list):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, r) for i, r in enumerate(r_list)))

    rings = "".join(f'<polygon points="{poly([radius * f] * n)}" fill="none" stroke="#d1d5db" stroke-dasharray="3 3"/>' for f in (0.33, 0.66, 1))
    spokes = "".join(f'<line x1="{cx}" y1="{cy}" x2="{point(i, radius)[0]:.1f}" y2="{point(i, radius)[1]:.1f}" stroke="#e5e7eb"/>' for i in range(n))
    data_r = [radius * max(v, 0.5) / 10 for v in values]
    dots = "".join(f'<circle cx="{point(i, r)[0]:.1f}" cy="{point(i, r)[1]:.1f}" r="3.5" fill="#16a34a"/>' for i, r in enumerate(data_r))
    badges = ""
    for i in range(n):  # little numbered circles around the chart
        x, y = point(i, radius + 22)
        badges += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="#fff" stroke="#e5e7eb"/>'
                   f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" font-size="11" fill="#374151">{i + 1}</text>')
    return (f'<svg viewBox="0 0 240 240" style="width:100%;max-width:230px;display:block;margin:0 auto">'
            f'{rings}{spokes}<polygon points="{poly(data_r)}" fill="rgba(34,197,94,0.25)" stroke="#16a34a" stroke-width="2"/>'
            f'{dots}{badges}</svg>')


def score_rows(items):
    """items = list of (name, value 0-10). Numbered rows with dotted line and coloured % chip."""
    rows = ""
    for i, (name, value) in enumerate(items):
        rows += (f'<div class="score-row"><span class="n">{i + 1}</span><span>{html.escape(name)}</span><span class="dots"></span>'
                 f'<span class="chip {level_for(value, 7, 4)}">{value * 10}%</span></div>')
    return rows


def ring_svg(pct):
    """Circular progress ring, pct from 0 to 100."""
    circ = 2 * math.pi * 34
    return (f'<svg viewBox="0 0 80 80" width="84" height="84"><circle cx="40" cy="40" r="34" fill="none" stroke="#e5e7eb" stroke-width="9"/>'
            f'<circle cx="40" cy="40" r="34" fill="none" stroke="#16a34a" stroke-width="9" stroke-linecap="round" '
            f'stroke-dasharray="{circ * pct / 100:.1f} {circ:.1f}" transform="rotate(-90 40 40)"/></svg>')


def promo(title, text, chip=None):
    """Green highlight card. If chip is given, the card is taller and shows a white pill at the bottom."""
    chip_html = f'<span class="promo-chip">{html.escape(chip)}</span>' if chip else ""
    return (f'<div class="promo{" tall" if chip else ""}"><div><h3>{html.escape(title)}</h3>'
            f'<p>{html.escape(text)}</p></div>{chip_html}</div>')


def hero(text):
    st.markdown(f'<div class="hero">{html.escape(text)}</div>', unsafe_allow_html=True)


# ---------- Tab 1: Find an Issue ----------
def tab_find():
    hero("Find an issue that matches your skills")

    left, right = st.columns([2, 1])
    with left:
        with card():
            picked = st.multiselect("Your skills", SKILLS, default=["python"], key="skills")
            extra = st.text_input("Other skills or topics (comma-separated)", placeholder="e.g. django, kotlin", key="extra_skills")
            find_clicked = st.button("Find issues", type="primary")
    with right:
        st.markdown(promo("No API keys yet?", "Tick Demo mode in the sidebar to try everything with sample data.", chip="👈 Demo mode is in the sidebar"),
                    unsafe_allow_html=True)

    if find_clicked:
        st.session_state["selected_notice"] = False
        skills = picked + [s.strip() for s in extra.split(",") if s.strip()]
        if demo_mode:
            st.session_state["found"] = DEMO["search_results"]
        elif not skills:
            st.warning("Pick at least one skill first.")
        else:
            try:
                with st.spinner("Searching GitHub for good first issues..."):
                    st.session_state["found"] = gh.search_good_first_issues(tuple(skills))
            except gh.GitHubError as e:
                st.error(str(e))

    if st.session_state.get("selected_notice"):
        st.success("✅ Issue saved! Now open the **Understand an Issue** tab.")

    found = st.session_state.get("found")
    if found is None:
        st.info("Pick your skills and click **Find issues** to see beginner-friendly issues.")
        return
    if not found:
        st.info("No fresh matching issues found. Try another skill or add a topic.")
        return

    # Three summary cards above the list
    best = max(int(r["score"]) for r in found)
    freshest = min(r["age_days"] for r in found)
    s1, s2, s3 = st.columns(3)
    s1.markdown(stat("Issues found", len(found), pill("READY", "green"), plain=True), unsafe_allow_html=True)
    s2.markdown(stat("Best match", f"{best}%", pill("TOP PICK", level_for(best, 80, 60)), plain=True), unsafe_allow_html=True)
    s3.markdown(stat("Freshest update", age_text(freshest), pill("ACTIVE", "green" if freshest <= 14 else "yellow"), plain=True), unsafe_allow_html=True)
    st.write("")

    for i, r in enumerate(found):
        with card():
            left, right = st.columns([5, 2])
            with left:
                st.markdown(f"**[{esc(r['title'])}]({r['url']})**")
                st.caption(f"{r['repo']} · {r['language'] or 'n/a'} · ⭐ {r['stars']} · updated {age_text(r['age_days'])} · {r['comments']} comments")
            with right:
                score = int(r["score"])
                st.markdown(pill(f"MATCH {score}/100", level_for(score, 80, 60)), unsafe_allow_html=True)
                st.button("Use this issue", key=f"use_{i}", on_click=use_issue, args=(r["url"],))


# ---------- Tab 2: Understand an Issue ----------
def analyze_issue(url):
    """Run the full pipeline for one issue and return everything the tabs need."""
    owner, repo, number = gh.parse_issue_url(url)
    issue = gh.get_issue(owner, repo, number)
    info = gh.get_repo_info(owner, repo)
    branch = info["default_branch"]

    tree = gh.get_file_tree(owner, repo, branch)
    candidates = gh.find_relevant_files(tree, issue["title"], issue["body"])
    files = []
    for path in candidates:
        try:
            files.append({"path": path, "content": gh.get_file_content(owner, repo, path)})
        except gh.NotFoundError:
            continue
    contributing = gh.get_contributing(owner, repo)

    explanation = llm.chat_json(*prompts.explain_issue(issue, info))
    where = llm.chat_json(*prompts.where_to_change(issue, files)) if files else {"files": []}
    allowed = {f["path"] for f in files}  # never show a file the model made up
    where_files = [f for f in where.get("files", []) if isinstance(f, dict) and f.get("path") in allowed]
    summary = llm.chat_json(*prompts.contributing_summary(contributing)) if contributing else None
    draft = llm.chat_json(*prompts.pr_draft(issue, contributing))

    return {
        "owner": owner, "repo": repo, "number": number, "default_branch": branch, "demo": False,
        "issue": issue, "repo_info": info, "explanation": explanation, "files": where_files,
        "contributing_summary": summary, "has_contributing": bool(contributing), "pr_draft": draft,
    }


def render_analysis(a):
    issue, info, ex = a["issue"], a["repo_info"], a["explanation"]
    st.markdown(f"### [{esc(issue['title'])}]({issue['html_url']})")
    st.caption(f"{a['owner']}/{a['repo']} · {info.get('language') or 'n/a'} · ⭐ {info.get('stars', 0)}")

    # Numbers used by the cards below
    difficulty = num(ex.get("difficulty"))
    mins = minutes(ex.get("estimated_minutes"))
    friendly = num(ex.get("beginner_friendly_score"))
    d_level = "green" if difficulty <= 3 else "yellow" if difficulty <= 6 else "orange"
    d_text = {"green": "EASY", "yellow": "MEDIUM", "orange": "HARD"}[d_level]
    if isinstance(mins, int):
        t_level = "green" if mins <= 60 else "yellow" if mins <= 180 else "orange"
    else:
        t_level = "yellow"
    t_text = {"green": "QUICK", "yellow": "MODERATE", "orange": "LONG"}[t_level]
    f_level = level_for(friendly, 7, 4)
    f_text = {"green": "GOOD", "yellow": "OKAY", "orange": "TOUGH"}[f_level]

    # Five simple scores for the radar chart (each from 0 to 10)
    speed = max(1, min(10, round(11 - mins / 30))) if isinstance(mins, int) else 5
    snapshot = [
        ("Ease", 10 - difficulty),
        ("Speed", speed),
        ("Beginner fit", friendly),
        ("Code clues", min(10, len(a["files"]) * 3 + 1)),
        ("Repo guidance", 9 if a.get("contributing_summary") else 3),
    ]

    left, right = st.columns([1, 2])
    with left:
        with card():
            st.markdown('<div class="card-title">Issue snapshot</div>', unsafe_allow_html=True)
            st.markdown(radar_svg([v for _, v in snapshot]) + score_rows(snapshot), unsafe_allow_html=True)
            st.caption("A quick estimate built from the AI's scores, the files found and the repo rules.")
    with right:
        with card():
            st.markdown('<div class="card-title">💡 What this issue is about</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.markdown(stat("Difficulty", f"{difficulty}/10", pill(d_text, d_level)), unsafe_allow_html=True)
            c2.markdown(stat("Time needed", f"~{mins} min", pill(t_text, t_level)), unsafe_allow_html=True)
            c3.markdown(stat("Beginner fit", f"{friendly}/10", pill(f_text, f_level)), unsafe_allow_html=True)
            st.write("")
            st.write(ex.get("simple_explanation", ""))
            st.markdown("**What success looks like**")
            st.write(ex.get("what_success_looks_like", ""))

    with card():
        st.markdown("#### 📂 Where to look")
        if not a["files"]:
            st.info("I couldn't confidently find the right files. Start by searching the repo for words from the issue title.")
        for f in a["files"]:
            with st.expander(f["path"]):
                st.write(f.get("reason", ""))
                st.markdown(f"**What to look for:** {f.get('what_to_look_for', '')}")
                st.markdown(f"[Open on GitHub](https://github.com/{a['owner']}/{a['repo']}/blob/{a['default_branch']}/{f['path']})")

    with card():
        st.markdown("#### 📜 Repo rules")
        summary = a.get("contributing_summary")
        if not summary:
            st.info("This repo has no CONTRIBUTING.md, so there are no written rules. Good defaults: keep your change small, "
                    "match the style of the code around it, and write a clear PR description. Be polite and patient. 🙂")
        else:
            for bullet in summary.get("bullets", []):
                st.markdown(f"- {bullet}")
            todo = summary.get("must_do_before_pr", [])
            if todo:
                st.markdown("**Do this before opening your PR:**")
                for item in todo:
                    st.markdown(f"- ☐ {item}")

    st.markdown(promo("Ready for your first PR?", "Open the PR Coach tab for your step-by-step plan."), unsafe_allow_html=True)


def tab_understand():
    hero("Understand an issue")
    with card():
        st.text_input("GitHub issue URL", key="issue_url", placeholder="https://github.com/owner/repo/issues/123")
        c1, c2, _ = st.columns([1, 1.7, 3])
        analyze = c1.button("Analyze", type="primary")
        c2.button("Try an example", on_click=fill_example)

    if analyze:
        url = st.session_state["issue_url"].strip()
        if not url:
            st.warning("Paste an issue link first, or click **Try an example**.")
        else:
            try:
                if demo_mode or url == SAMPLE_URL:
                    st.session_state["analysis"] = DEMO
                else:
                    with st.spinner("Reading the issue and repo, then asking the AI mentor (can take a minute)..."):
                        st.session_state["analysis"] = analyze_issue(url)
            except (ValueError, gh.GitHubError, llm.LLMError) as e:
                st.error(str(e))
            except Exception as e:  # last resort so the demo never shows a stack trace
                st.error(f"Something unexpected went wrong ({type(e).__name__}). Please try again.")

    if st.session_state.get("analysis"):
        render_analysis(st.session_state["analysis"])
    else:
        st.info("Paste an issue link and click **Analyze**, or pick one in the **Find an Issue** tab.")


# ---------- Tab 3: PR Coach ----------
def progress_html(done, total):
    """Ring + big percentage + striped bar (green part = finished steps)."""
    pct = round(100 * done / total) if total else 0
    return (f'<div class="progress-card">{ring_svg(pct)}<div class="main">'
            f'<div class="stat-top"><span class="stat-label">Your progress</span>'
            f'{pill(f"{done} OF {total} STEPS", "green" if done == total else "black")}</div>'
            f'<div class="stat-num">{pct}%</div><div class="bar"><span style="width:{pct}%"></span></div></div></div>')


def tab_coach():
    a = st.session_state.get("analysis")
    if not a:
        hero("Your PR plan")
        st.info("Analyze an issue first (in the **Understand an Issue** tab) and your step-by-step plan will show up here.")
        return

    hero(f"Your plan for #{a['number']}")
    st.caption(a["issue"]["title"])
    with card():
        username = st.text_input("Your GitHub username", key="gh_username", placeholder="octocat").strip()
        if not username:
            st.caption("Enter your username to get commands you can copy and paste as-is.")

    if a.get("demo"):  # demo steps contain a {username} placeholder
        fill = username or "YOUR-USERNAME"
        steps = [
            {**s, "command": s["command"].replace("{username}", fill) if s.get("command") else None,
             "link": s["link"].replace("{username}", fill) if s.get("link") else None}
            for s in a["steps"]
        ]
    else:
        steps = coach.generate_steps(a["owner"], a["repo"], a["number"], a["issue"]["title"], a["default_branch"], username)

    progress = st.empty()  # filled after the checkboxes are drawn
    done = 0
    for i, step in enumerate(steps):
        step_key = f"step_{a['repo']}_{a['number']}_{i}"
        with card(done=bool(st.session_state.get(step_key))):  # finished steps turn light green
            if st.checkbox(f"**{i + 1}. {step['title']}**", key=step_key):
                done += 1
            st.write(step["explanation"])
            if step.get("command"):
                st.code(step["command"], language="bash")
            if step.get("link"):
                st.markdown(f"🔗 [{step.get('link_label', 'Open')}]({step['link']})")
    progress.markdown(progress_html(done, len(steps)), unsafe_allow_html=True)
    if done == len(steps):
        st.success("🎉 You did it! Your first pull request is on its way.")

    draft = a.get("pr_draft")
    if draft:
        st.markdown("### ✍️ Your PR draft")
        st.caption("Copy these into the pull request form. Fill in anything in [brackets] after you've made your change.")
        st.code(draft.get("title", ""), language=None)
        st.code(draft.get("description", ""), language="markdown")


tab1, tab2, tab3 = st.tabs(["Find an Issue", "Understand an Issue", "PR Coach"])
with tab1:
    tab_find()
with tab2:
    tab_understand()
with tab3:
    tab_coach()
