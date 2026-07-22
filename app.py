"""
app.py

Purpose
-------
Streamlit frontend for the Intelligent Credit Decision Support Platform.

Design language (v3)
---------------------
Synthesized from three references given over this project:
  1. A dedicated UI/UX mockup of this exact platform (page flow: Login,
     Dashboard, Loan Prediction, Prediction Result, SHAP Analysis, Ask
     AI, AI Conversation, Simulation, Knowledge Assistant, History).
  2. A two-tier icon-rail + accordion-group sidebar with a persistent
     floating "Ask AI" action button.
  3. A dark glassmorphic dashboard (RonDesignLab #09): translucent
     blurred cards, white text on charcoal, colorful accent dots,
     pill-shaped nav chips, bold big stat numerals.

Two deliberate adaptations, not literal copies:
  - Reference 3 blurs a stock photo background. This uses a pure-CSS
    gradient mesh instead — same mood, no image licensing risk, and it
    reads as "bank" rather than "coffee shop."
  - Reference 3's all-dark-glass look is stunning for glanceable stat
    surfaces but hurts legibility for a 19-field form and paragraph-
    length AI answers. So: dark glass for chrome/stats/AI, clean light
    cards for dense forms, tables, and long text.

Module architecture reflected by this UI
------------------------------------------
Module A (Loan Prediction) and Module B (Knowledge Assistant) are
independent, always-reachable destinations. Module C (Decision
Intelligence) is NOT a nav destination — it lives entirely behind the
floating "Ask AI" button. Opening it NEVER auto-asks a question (fixed
from an earlier version of this UI) — it always opens to a greeting
and suggested questions, and waits for the user to choose. Every
question typed there goes through the unified /api/v1/query endpoint,
and the UI visibly shows the Intent Router's decision ("Identifying
intent…" -> "Identified: Simulation question") before the answer.

Login
-----
Session-gated only: a plain username/password string match against
Musab / musab123. This is NOT real authentication — no hashing, no
user store, no backend auth endpoint. Fine for a local prototype;
flagging clearly in case this is ever deployed anywhere reachable by
anyone else.

Run the backend first, in a separate terminal, from the project root:

    uvicorn backend.main:app --reload --port 8000

Then run this file:

    streamlit run app.py

Dependencies (add to requirements.txt if not already present):

    streamlit>=1.37
    requests

Author
------
Intelligent Credit Decision Support Platform
"""

import math
import time
import uuid

import requests
import streamlit as st


# ==========================================================
# CONFIG
# ==========================================================

DEFAULT_API_BASE = "http://127.0.0.1:8000"
LOGIN_USERNAME = "Musab"
LOGIN_PASSWORD = "musab123"

APPLICANT_FIELDS = [
    {"k": "loan_amnt", "label": "Loan amount ($)", "type": "number", "default": 12000},
    {"k": "term", "label": "Term (months)", "type": "select", "options": [36, 60], "default": 36},
    {"k": "int_rate", "label": "Interest rate (%)", "type": "number", "default": 13.33, "step": 0.01},
    {"k": "sub_grade", "label": "Sub-grade", "type": "select",
     "options": [f"{l}{n}" for l in "ABCDEFG" for n in range(1, 6)], "default": "B3"},
    {"k": "emp_length", "label": "Employment length (yrs)", "type": "number", "default": 7},
    {"k": "home_ownership", "label": "Home ownership", "type": "select",
     "options": ["MORTGAGE", "RENT", "OWN", "OTHER"], "default": "MORTGAGE"},
    {"k": "verification_status", "label": "Verification status", "type": "select",
     "options": ["Verified", "Source Verified", "Not Verified"], "default": "Verified"},
    {"k": "annual_inc", "label": "Annual income ($)", "type": "number", "default": 71000},
    {"k": "purpose", "label": "Loan purpose", "type": "select",
     "options": ["debt_consolidation", "credit_card", "home_improvement", "major_purchase",
                 "medical", "car", "other"], "default": "debt_consolidation"},
    {"k": "dti", "label": "DTI (%)", "type": "number", "default": 12.0, "step": 0.1},
    {"k": "open_acc", "label": "Open accounts", "type": "number", "default": 10},
    {"k": "pub_rec", "label": "Public records", "type": "number", "default": 0},
    {"k": "revol_bal", "label": "Revolving balance ($)", "type": "number", "default": 6000},
    {"k": "revol_util", "label": "Revolving utilization (%)", "type": "number", "default": 41.0, "step": 0.1},
    {"k": "total_acc", "label": "Total accounts", "type": "number", "default": 28},
    {"k": "initial_list_status", "label": "Initial list status", "type": "select",
     "options": ["w", "f"], "default": "w"},
    {"k": "application_type", "label": "Application type", "type": "select",
     "options": ["INDIVIDUAL", "JOINT"], "default": "INDIVIDUAL"},
    {"k": "mort_acc", "label": "Mortgage accounts", "type": "number", "default": 2},
    {"k": "pub_rec_bankruptcies", "label": "Bankruptcies on record", "type": "number", "default": 0},
]

GRADE_COLORS = {
    "A": "#34D399", "B": "#5B8DEF", "C": "#FBBF24",
    "D": "#FB923C", "E": "#F87171", "F": "#EF4444", "G": "#B91C1C",
}

INTENT_META = {
    "DECISION":   {"label": "Decision question",        "color": "#5B8DEF"},
    "SIMULATION": {"label": "Simulation question",       "color": "#A78BFA"},
    "KNOWLEDGE":  {"label": "Policy knowledge question", "color": "#34D399"},
    "GENERAL":    {"label": "General question",          "color": "#9CA3AF"},
}

NAV_GROUPS = {
    "workspace": {
        "icon": "🏛",
        "label": "Workspace",
        "items": [("Dashboard", "🏠"), ("Loan Prediction", "📝"), ("Knowledge Assistant", "📚")],
    },
    "records": {
        "icon": "🗂",
        "label": "Records",
        "items": [("History", "🕐")],
    },
    "account": {
        "icon": "⚙",
        "label": "Account",
        "items": [("Settings", "⚙")],
    },
}


# ==========================================================
# SESSION STATE
# ==========================================================

def init_state():
    defaults = {
        "authenticated": False,
        "api_base": DEFAULT_API_BASE,
        "session_id": "sess-" + uuid.uuid4().hex[:8],
        "page": "Dashboard",
        "nav_group_open": "workspace",
        "history": [],
        "last_applicant": None,
        "last_prediction": None,
        "prob_trend": [],
        "decision_chat": [],
        "kb_chat": [],
        "pending_question": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ==========================================================
# API HELPERS
# ==========================================================

class ApiError(Exception):
    pass


def api_post(path: str, body: dict) -> dict:
    url = st.session_state.api_base.rstrip("/") + path
    try:
        resp = requests.post(url, json=body, timeout=90)
    except requests.exceptions.RequestException as error:
        raise ApiError(f"Could not reach {url}: {error}")

    data = {}
    try:
        data = resp.json()
    except ValueError:
        pass

    if not resp.ok:
        detail = data.get("detail") if isinstance(data, dict) else None
        raise ApiError(detail if isinstance(detail, str) else str(detail or f"HTTP {resp.status_code}"))

    return data


def check_health() -> bool:
    try:
        resp = requests.get(st.session_state.api_base.rstrip("/") + "/health", timeout=4)
        data = resp.json()
        return bool(resp.ok and data.get("model_loaded"))
    except Exception:
        return False


# ==========================================================
# VISUAL HELPERS — donut gauge & sparkline, pure inline SVG
# ==========================================================

def donut_svg(pct: float, color: str, size: int = 108, stroke: int = 10) -> str:
    pct = max(0, min(100, pct))
    r = (size - stroke) / 2
    c = 2 * math.pi * r
    offset = c * (1 - pct / 100)
    cx = cy = size / 2
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="{stroke}"/>
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}"
                stroke-linecap="round" stroke-dasharray="{c:.2f}" stroke-dashoffset="{offset:.2f}"
                transform="rotate(-90 {cx} {cy})"/>
        <text x="{cx}" y="{cy + 7}" text-anchor="middle" font-size="21" font-weight="800" fill="white"
              font-family="Inter, sans-serif">{pct:.0f}%</text>
    </svg>"""


def sparkline_svg(values, color: str, w: int = 92, h: int = 30) -> str:
    if len(values) < 2:
        return (f'<svg width="{w}" height="{h}">'
                 f'<line x1="4" y1="{h/2}" x2="{w-4}" y2="{h/2}" stroke="{color}" '
                 f'stroke-width="2" stroke-dasharray="3,3" opacity="0.35"/></svg>')
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = 4 + (w - 8) * (i / (n - 1))
        y = h - 4 - (h - 8) * ((v - lo) / rng)
        pts.append(f"{x:.1f},{y:.1f}")
    points = " ".join(pts)
    return (f'<svg width="{w}" height="{h}"><polyline points="{points}" fill="none" '
            f'stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


# ==========================================================
# STYLE
# ==========================================================

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root{
        --glass-bg: rgba(24,28,40,0.60);
        --glass-bg-soft: rgba(24,28,40,0.40);
        --glass-border: rgba(255,255,255,0.09);
        --text-on-glass: #F5F6FA;
        --text-on-glass-soft: rgba(245,246,250,0.62);
        --light-card: #FFFFFF;
        --light-border: #ECEDF0;
        --text: #14161A;
        --text-soft: #6B7280;
        --blue: #5B8DEF; --blue-bg: rgba(91,141,239,0.14);
        --green: #34D399; --green-bg: rgba(52,211,153,0.14);
        --purple: #A78BFA; --purple-bg: rgba(167,139,250,0.14);
        --amber: #FBBF24; --amber-bg: rgba(251,191,36,0.14);
        --red: #F87171; --red-bg: rgba(248,113,113,0.14);
    }

    html, body, [class*="css"]{ font-family:'Inter', system-ui, sans-serif; }

    .stApp{
        background:
            radial-gradient(circle at 12% 18%, rgba(91,141,239,0.22), transparent 42%),
            radial-gradient(circle at 88% 12%, rgba(167,139,250,0.18), transparent 46%),
            radial-gradient(circle at 55% 92%, rgba(52,211,153,0.10), transparent 42%),
            linear-gradient(165deg, #0A0E19 0%, #121729 55%, #0A0E19 100%);
        background-attachment: fixed;
    }
    [data-testid="stHeader"]{ background:transparent; }
    .block-container{ padding-top:1.6rem; max-width:1300px; }

    [data-testid="stSidebar"]{
        background: var(--glass-bg);
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        border-right: 1px solid var(--glass-border);
    }
    [data-testid="stSidebar"] *{ color: var(--text-on-glass); }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{ color: var(--text-on-glass-soft); }

    .rail-btn button{
        background: transparent !important; border: 1px solid transparent !important;
        color: var(--text-on-glass-soft) !important; font-size: 18px !important;
        padding: 10px 0 !important; border-radius: 12px !important; width: 100% !important;
    }
    .rail-btn-active button{
        background: rgba(91,141,239,0.20) !important; border: 1px solid rgba(91,141,239,0.4) !important;
        color: white !important;
    }

    .nav-item-btn button{
        background: transparent !important; border: none !important; text-align:left !important;
        color: var(--text-on-glass-soft) !important; font-weight:500 !important; font-size:13px !important;
        padding: 8px 10px !important; border-radius: 10px !important; width:100% !important;
    }
    .nav-item-active button{
        background: rgba(255,255,255,0.10) !important; color: white !important; font-weight:600 !important;
    }
    .nav-group-header button{
        background:transparent !important; border:none !important; color:var(--text-on-glass-soft) !important;
        font-size:10.5px !important; font-weight:700 !important; text-transform:uppercase; letter-spacing:.06em;
        padding:4px 10px !important; text-align:left !important;
    }

    .main .stButton>button{
        border-radius:12px; border:1px solid var(--light-border); background:var(--light-card);
        color:var(--text); font-weight:600; font-size:13.5px; padding:9px 18px;
    }
    .main .stButton>button:hover{ border-color:#D9DBE0; background:#F8F9FA; }
    .main .stButton>button[kind="primary"]{ background:var(--blue); color:#fff; border-color:var(--blue); }
    .main .stButton>button[kind="primary"]:hover{ background:#4A78D9; }

    .st-key-floating_ai_btn{ position: fixed; bottom: 30px; right: 34px; z-index: 9998; width: auto; }
    .st-key-floating_ai_btn button{
        width:60px; height:60px; border-radius:50%; background:linear-gradient(145deg,#1B2033,#0E1220) !important;
        border:1px solid rgba(255,255,255,0.14) !important; color:white !important; font-size:22px !important;
        box-shadow: 0 12px 30px rgba(0,0,0,0.45), 0 0 0 1px rgba(91,141,239,0.15) !important;
    }
    .st-key-floating_ai_btn button:hover{ background:linear-gradient(145deg,#232A44,#141a2e) !important; }

    .glass-card{
        background: var(--glass-bg); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
        border:1px solid var(--glass-border); border-radius:24px; padding:22px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.35); color: var(--text-on-glass); margin-bottom:16px;
    }
    .glass-card *{ color: var(--text-on-glass); }
    .glass-soft{ color: var(--text-on-glass-soft) !important; }

    .light-card{
        background: var(--light-card); border:1px solid var(--light-border); border-radius:22px;
        padding:22px; box-shadow: 0 1px 2px rgba(16,17,20,.04), 0 8px 24px rgba(16,17,20,.06); margin-bottom:16px;
    }
    [data-testid="stForm"]{
        background: var(--light-card); border:1px solid var(--light-border); border-radius:22px;
        padding:22px; box-shadow: 0 1px 2px rgba(16,17,20,.04), 0 8px 24px rgba(16,17,20,.06);
    }

    .hero-title{ font-size:26px; font-weight:800; letter-spacing:-.02em; color:white; margin-bottom:4px; }
    .hero-sub{ font-size:13.5px; color:rgba(255,255,255,0.55); margin-bottom:20px; }

    .cta-card{ border-radius:22px; padding:22px; height:100%; }
    .cta-card h3{ font-size:16px; font-weight:800; margin:10px 0 4px; color:white; }
    .cta-card p{ font-size:12px; color:rgba(255,255,255,0.6); }
    .cta-icon{ width:44px; height:44px; border-radius:13px; display:flex; align-items:center; justify-content:center; font-size:20px; }

    .stat-num{ font-size:24px; font-weight:800; color:white; }
    .stat-lbl{ font-size:11px; color:rgba(255,255,255,0.55); font-weight:600; text-transform:uppercase; letter-spacing:.04em; }

    .sc-badge{ padding:8px 16px; border-radius:12px; font-size:15px; font-weight:800; display:inline-block; }
    .sc-badge-approved{ background:var(--green-bg); color:var(--green); }
    .sc-badge-rejected{ background:var(--red-bg); color:var(--red); }

    .sc-pill-intent{ padding:4px 12px; border-radius:999px; font-size:11px; font-weight:700; display:inline-block; margin-bottom:8px; }

    .sc-shap-row{ display:flex; align-items:center; gap:10px; margin-bottom:10px; }
    .sc-shap-name{ width:120px; font-size:12px; font-weight:600; flex-shrink:0; }
    .sc-shap-track{ flex:1; height:8px; background:rgba(255,255,255,0.08); border-radius:5px; position:relative; overflow:hidden; }
    .sc-shap-fill{ position:absolute; top:0; bottom:0; border-radius:5px; }
    .sc-shap-mid{ position:absolute; left:50%; top:0; bottom:0; width:1px; background:rgba(255,255,255,0.2); z-index:1; }
    .sc-shap-val{ width:64px; text-align:right; font-size:11.5px; font-weight:600; flex-shrink:0; }
    .sc-shap-row.on-light .sc-shap-name, .sc-shap-row.on-light .sc-shap-val{ color:#14161A; }
    .sc-shap-row.on-light .sc-shap-track{ background:#F1F2F4; }
    .sc-shap-row.on-light .sc-shap-mid{ background:#D9DBE0; }

    .sc-table{ width:100%; border-collapse:collapse; }
    .sc-table th{ text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--text-soft);
                  font-weight:700; padding:0 10px 10px; border-bottom:1px solid var(--light-border); }
    .sc-table td{ padding:12px 10px; border-bottom:1px solid var(--light-border); font-size:13px; color:var(--text); }
    .sc-table tr:last-child td{ border-bottom:none; }
    .sc-pill{ padding:4px 10px; border-radius:999px; font-size:11px; font-weight:600; display:inline-block; }
    .sc-pill-approved{ background:#111214; color:#fff; }
    .sc-pill-rejected{ background:#FDEDED; color:#DC2626; }
    .sc-pill-pending{ background:#F1F2F4; color:#6B7280; }
    .sc-muted{ color:var(--text-soft); }

    .sc-empty{ text-align:center; padding:36px 16px; color:rgba(255,255,255,0.45); font-size:13px; }
    .sc-empty.on-light{ color:#8B8F98; }

    .sc-source-chip{ font-size:10.5px; padding:3px 8px; border-radius:999px; background:rgba(52,211,153,0.14); color:#34D399;
                      font-weight:600; margin:6px 6px 0 0; display:inline-block; }

    .login-wrap{ display:flex; align-items:center; justify-content:center; min-height:80vh; }
    </style>
    """, unsafe_allow_html=True)


# ==========================================================
# SMALL HELPERS
# ==========================================================

def grade_color(sub_grade):
    if not sub_grade:
        return "#9CA3AF"
    return GRADE_COLORS.get(str(sub_grade)[0].upper(), "#6B7280")


def time_ago(ts):
    s = int(time.time() - ts)
    if s < 60:
        return f"{s}s ago"
    if s < 3600:
        return f"{s // 60}m ago"
    if s < 86400:
        return f"{s // 3600}h ago"
    return f"{s // 86400}d ago"


# ==========================================================
# LOGIN
# ==========================================================

def render_login():
    inject_css()
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    col = st.columns([1, 1.1, 1])[1]
    with col:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:36px 30px;">
            <div style="width:52px; height:52px; border-radius:16px; background:linear-gradient(145deg,#5B8DEF,#3E6BD1);
                        display:flex; align-items:center; justify-content:center; margin:0 auto 14px; font-size:24px;">🛡</div>
            <div style="font-size:19px; font-weight:800; color:white;">STRATUM CAPITAL BANK</div>
            <div style="font-size:12px; color:rgba(255,255,255,0.55); margin-top:2px; margin-bottom:22px;">
                Intelligent Credit Decision Support Platform</div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", key="login_user", placeholder="Enter your username")
        password = st.text_input("Password", key="login_pass", type="password", placeholder="Enter your password")

        if st.button("Login", type="primary", use_container_width=True):
            if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================================
# SIDEBAR — icon rail + accordion panel
# ==========================================================

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; padding:6px 4px 16px;">
            <div style="width:36px; height:36px; border-radius:12px; background:linear-gradient(145deg,#5B8DEF,#3E6BD1);
                        display:flex; align-items:center; justify-content:center; font-size:17px; flex-shrink:0;">🛡</div>
            <div>
                <div style="font-weight:800; font-size:14.5px; color:white; letter-spacing:-.01em;">STRATUM</div>
                <div style="font-size:10px; color:rgba(255,255,255,0.5); font-weight:500;">CAPITAL BANK</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; padding:10px; border-radius:14px;
                    background:rgba(255,255,255,0.05); margin-bottom:16px;">
            <div style="width:32px; height:32px; border-radius:50%; background:linear-gradient(145deg,#A78BFA,#7C5CDB);
                        display:flex; align-items:center; justify-content:center; font-weight:700; font-size:12px; color:white;">LO</div>
            <div style="flex:1;">
                <div style="font-size:12.5px; font-weight:600; color:white;">Loan Officer</div>
                <div style="font-size:10px; color:rgba(255,255,255,0.5);">Underwriting Desk</div>
            </div>
            <div style="color:rgba(255,255,255,0.4); font-size:11px;">▾</div>
        </div>
        """, unsafe_allow_html=True)

        rail_col, panel_col = st.columns([1, 3.4])

        with rail_col:
            for key, group in NAV_GROUPS.items():
                active = st.session_state.nav_group_open == key
                st.markdown(f'<div class="rail-btn{" rail-btn-active" if active else ""}">', unsafe_allow_html=True)
                if st.button(group["icon"], key=f"rail_{key}"):
                    st.session_state.nav_group_open = key
                    if st.session_state.page not in [i[0] for i in group["items"]]:
                        st.session_state.page = group["items"][0][0]
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        with panel_col:
            open_group = NAV_GROUPS[st.session_state.nav_group_open]
            st.markdown(f'<div class="nav-group-header"><button disabled style="opacity:1 !important;">{open_group["label"]}</button></div>', unsafe_allow_html=True)
            for label, icon in open_group["items"]:
                is_active = st.session_state.page == label
                st.markdown(f'<div class="nav-item-btn{" nav-item-active" if is_active else ""}">', unsafe_allow_html=True)
                if st.button(f"{icon}  {label}", key=f"nav_{label}"):
                    st.session_state.page = label
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        status_ok = check_health()
        dot_color = "#34D399" if status_ok else "#F87171"
        status_txt = "Connected · model ready" if status_ok else "Offline · backend unreachable"
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:7px; padding:8px 10px; border-radius:10px;
                    background:rgba(255,255,255,0.05); font-size:11px; color:rgba(255,255,255,0.6);">
            <span style="width:7px; height:7px; border-radius:50%; background:{dot_color};
                         box-shadow:0 0 0 3px {dot_color}22;"></span>
            {status_txt}
        </div>
        """, unsafe_allow_html=True)

        if st.button("↩  Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.rerun()


# ==========================================================
# FLOATING ASK AI BUTTON + MODAL (Module C entry point)
# ==========================================================

def render_floating_ai_button():
    with st.container(key="floating_ai_btn"):
        if st.button("✦", key="ai_fab", help="Ask AI"):
            open_ai_dialog()


@st.dialog("Ask AI — Decision Intelligence", width="large")
def open_ai_dialog():
    render_module_c_chat()


def render_module_c_chat():
    has_prediction = st.session_state.last_prediction is not None

    if not st.session_state.decision_chat:
        if has_prediction:
            p = st.session_state.last_prediction
            st.markdown(f"""
            <div style="display:flex; gap:10px; align-items:flex-start; margin-bottom:14px;">
                <div style="width:34px; height:34px; border-radius:50%; background:linear-gradient(145deg,#5B8DEF,#3E6BD1);
                            display:flex; align-items:center; justify-content:center; font-size:15px; flex-shrink:0;">✦</div>
                <div style="background:#F5F6F8; border-radius:14px; border-bottom-left-radius:4px; padding:12px 15px; font-size:13.5px;">
                    Hi — I'm your AI Decision Assistant.<br>
                    This applicant was <b>{p['prediction']}</b>. Ask me why, what would change the
                    outcome, or a policy question — I'll figure out which one automatically.
                </div>
            </div>
            """, unsafe_allow_html=True)
            chips = [
                f"Why was this applicant {p['prediction'].lower()}?",
                "What would improve this applicant's chances?",
                "What if annual income increases by 30%?",
            ]
        else:
            st.markdown("""
            <div style="display:flex; gap:10px; align-items:flex-start; margin-bottom:14px;">
                <div style="width:34px; height:34px; border-radius:50%; background:linear-gradient(145deg,#5B8DEF,#3E6BD1);
                            display:flex; align-items:center; justify-content:center; font-size:15px; flex-shrink:0;">✦</div>
                <div style="background:#F5F6F8; border-radius:14px; border-bottom-left-radius:4px; padding:12px 15px; font-size:13.5px;">
                    Hi — I'm your AI Decision Assistant.<br>
                    No prediction is on file yet, so I can answer general bank-policy questions
                    right now. Run a prediction from <b>Loan Prediction</b> to ask about a
                    specific decision.
                </div>
            </div>
            """, unsafe_allow_html=True)
            chips = [
                "What is the maximum allowed DTI?",
                "What does Sub-Grade B3 mean?",
                "What are the conditions for a policy exception?",
            ]

        chip_cols = st.columns(len(chips))
        for col, chip in zip(chip_cols, chips):
            with col:
                if st.button(chip, key=f"aichip_{chip[:16]}"):
                    st.session_state.pending_question = chip
                    st.rerun()

    for msg in st.session_state.decision_chat:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and msg.get("intent"):
                render_intent_chip(msg["intent"])
            st.write(msg["content"])
            if msg.get("extra"):
                render_intent_extra(msg["intent"], msg["extra"])

    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None

        with st.chat_message("user"):
            st.write(question)
        st.session_state.decision_chat.append({"role": "user", "content": question})

        with st.chat_message("assistant"):
            with st.status("🔍 Identifying intent…", expanded=False) as status:
                error_text = None
                data = None
                intent = None
                try:
                    data = api_post("/api/v1/query", {
                        "question": question,
                        "session_id": st.session_state.session_id,
                    })
                    intent = data.get("intent", "GENERAL")
                    meta = INTENT_META.get(intent, INTENT_META["GENERAL"])
                    status.update(label=f"✅ Identified: {meta['label']}", state="complete")
                except ApiError as e:
                    error_text = str(e)
                    status.update(label="❌ Request failed", state="error")

            if error_text:
                st.write(f"Sorry — that request failed: {error_text}")
                st.session_state.decision_chat.append({"role": "assistant", "content": f"Sorry — that request failed: {error_text}"})
            else:
                render_intent_chip(intent)
                answer = data.get("answer", "No response returned.")
                st.write(answer)
                extra = extract_intent_extra(intent, data)
                if extra:
                    render_intent_extra(intent, extra)
                st.session_state.decision_chat.append({"role": "assistant", "content": answer, "intent": intent, "extra": extra})
                st.session_state.history.insert(0, {"type": "ai_turn", "intent": intent, "summary": question, "ts": time.time()})
        st.rerun()

    q = st.chat_input("Ask a question…", key="module_c_input")
    if q:
        st.session_state.pending_question = q
        st.rerun()


def render_intent_chip(intent):
    meta = INTENT_META.get(intent, INTENT_META["GENERAL"])
    st.markdown(
        f'<span class="sc-pill-intent" style="background:{meta["color"]}22; color:{meta["color"]};">{meta["label"]}</span>',
        unsafe_allow_html=True,
    )


def extract_intent_extra(intent, data):
    if intent == "SIMULATION" and data.get("simulation"):
        return {"simulation": data["simulation"]}
    if intent == "KNOWLEDGE" and data.get("retrieved_documents"):
        sources = []
        for d in data["retrieved_documents"]:
            meta = d.get("document", {}).get("metadata", {})
            src = str(meta.get("source", "")).replace("\\", "/").split("/")[-1]
            page = meta.get("page_label", meta.get("page", "?"))
            sources.append(f"{src} · p.{page}")
        return {"sources": sources}
    if intent == "DECISION" and data.get("prediction", {}).get("top_features"):
        return {"top_features": data["prediction"]["top_features"]}
    return None


def render_intent_extra(intent, extra):
    if "simulation" in extra:
        sim = extra["simulation"]
        o, s = sim.get("original", {}), sim.get("simulation", {})
        c = sim.get("comparison", {})
        diff = c.get("default_probability_difference", 0) or 0
        delta = ("No change", "#9CA3AF") if diff == 0 else (("Higher risk", "#F87171") if diff > 0 else ("Lower risk", "#34D399"))
        col_a, col_b = st.columns(2)
        for col, label, res in [(col_a, "Current", o), (col_b, "Simulated", s)]:
            if not res:
                continue
            badge_cls = "sc-badge-approved" if res.get("prediction") == "Approved" else "sc-badge-rejected"
            with col:
                st.markdown(f"""
                <div style="border:1px solid #ECEDF0; border-radius:14px; padding:14px; margin-top:6px;">
                    <div style="font-size:10.5px; text-transform:uppercase; letter-spacing:.04em; color:#8B8F98; margin-bottom:8px;">{label}</div>
                    <span class="sc-badge {badge_cls}" style="font-size:12px; padding:5px 10px;">{res.get("prediction", "—")}</span>
                    <div style="display:flex; gap:14px; margin-top:10px;">
                        <div><div style="font-size:14px; font-weight:800;">{(res.get("repayment_probability") or 0)*100:.1f}%</div><div style="font-size:9.5px; color:#8B8F98;">Repay</div></div>
                        <div><div style="font-size:14px; font-weight:800;">{(res.get("default_probability") or 0)*100:.1f}%</div><div style="font-size:9.5px; color:#8B8F98;">Default</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown(f'<span style="background:{delta[1]}22; color:{delta[1]}; padding:3px 10px; border-radius:999px; font-size:11.5px; font-weight:700;">{delta[0]}</span>', unsafe_allow_html=True)

    if "sources" in extra:
        st.markdown(" ".join(f'<span class="sc-source-chip">{s}</span>' for s in extra["sources"]), unsafe_allow_html=True)

    if "top_features" in extra:
        render_shap_bars(extra["top_features"], on_light=True)


def render_shap_bars(features, on_light=False):
    rows = ""
    for f in features:
        is_pos = f["shap"] >= 0
        magnitude = min(abs(f["shap"]) * 220, 50)
        fill_style = f"right:50%; width:{magnitude}%; background:#F87171;" if is_pos else f"left:50%; width:{magnitude}%; background:#34D399;"
        rows += f"""
        <div class="sc-shap-row {'on-light' if on_light else ''}">
            <div class="sc-shap-name">{f["feature"]}</div>
            <div class="sc-shap-track"><div class="sc-shap-mid"></div><div class="sc-shap-fill" style="{fill_style}"></div></div>
            <div class="sc-shap-val">{f["value"]}</div>
        </div>"""
    st.markdown(rows, unsafe_allow_html=True)


# ==========================================================
# DASHBOARD
# ==========================================================

def render_dashboard():
    st.markdown('<div class="hero-title">Welcome back, Loan Officer 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">How can we help you today?</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="glass-card cta-card">
            <div class="cta-icon" style="background:var(--blue-bg); color:var(--blue);">📝</div>
            <h3>Loan Prediction</h3>
            <p>Predict a loan outcome using the trained credit risk model.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Loan Prediction →", key="cta_predict", use_container_width=True):
            st.session_state.nav_group_open = "workspace"
            st.session_state.page = "Loan Prediction"
            st.rerun()
    with c2:
        st.markdown("""
        <div class="glass-card cta-card">
            <div class="cta-icon" style="background:var(--green-bg); color:var(--green);">📚</div>
            <h3>Knowledge Assistant</h3>
            <p>Ask about bank policy, lending guidelines, or credit grading rules.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Assistant →", key="cta_kb", use_container_width=True):
            st.session_state.nav_group_open = "workspace"
            st.session_state.page = "Knowledge Assistant"
            st.rerun()

    st.write("")

    h = st.session_state.history
    decisions = [x for x in h if x["type"] == "decision"]
    ai_turns = [x for x in h if x["type"] == "ai_turn"]
    approved = sum(1 for x in decisions if x["prediction"] == "Approved")
    rejected = sum(1 for x in decisions if x["prediction"] == "Rejected")
    simulations = sum(1 for x in ai_turns if x.get("intent") == "SIMULATION")

    stats = [
        ("Applications", len(decisions), "#5B8DEF"),
        ("Approved", approved, "#34D399"),
        ("Rejected", rejected, "#F87171"),
        ("AI conversations", len(ai_turns), "#A78BFA"),
        ("Simulations", simulations, "#FBBF24"),
    ]
    cols = st.columns(5)
    for col, (label, value, color) in zip(cols, stats):
        with col:
            spark = sparkline_svg(st.session_state.prob_trend[-8:], color) if label == "Applications" else sparkline_svg([], color)
            st.markdown(f"""
            <div class="glass-card" style="padding:16px;">
                <div class="stat-lbl">{label}</div>
                <div style="display:flex; align-items:flex-end; justify-content:space-between; margin-top:6px;">
                    <div class="stat-num">{value}</div>
                    {spark}
                </div>
            </div>
            """, unsafe_allow_html=True)

    left, right = st.columns([1.5, 1])
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:700; font-size:14.5px; margin-bottom:14px;">Recent applications</div>', unsafe_allow_html=True)
        recent = decisions[:6]
        if not recent:
            st.markdown('<div class="sc-empty">No applications yet this session.</div>', unsafe_allow_html=True)
        else:
            rows = ""
            for r in recent:
                pill_color = "#34D399" if r["prediction"] == "Approved" else "#F87171"
                rows += f"""
                <div style="display:flex; align-items:center; gap:10px; padding:9px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
                    <div style="width:28px; height:28px; border-radius:9px; background:{grade_color(r.get('sub_grade'))};
                                display:flex; align-items:center; justify-content:center; font-size:10.5px; font-weight:700; color:white;">{r.get('sub_grade','—')[:2]}</div>
                    <div style="flex:1;">
                        <div style="font-size:12.5px; font-weight:600;">{r['applicant_label']}</div>
                        <div style="font-size:10.5px; color:rgba(255,255,255,0.45);">${r.get('loan_amnt',0):,.0f} · {time_ago(r['ts'])}</div>
                    </div>
                    <span style="background:{pill_color}22; color:{pill_color}; padding:3px 10px; border-radius:999px; font-size:10.5px; font-weight:700;">{r['prediction']}</span>
                </div>"""
            st.markdown(rows, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:700; font-size:14.5px; margin-bottom:14px;">Needs manual review</div>', unsafe_allow_html=True)
        review_items = [x for x in decisions if x["prediction"] == "Rejected" or (0.35 < x["default"] < 0.6)][:5]
        if not review_items:
            st.markdown('<div class="sc-empty">Nothing flagged right now.</div>', unsafe_allow_html=True)
        else:
            rows = ""
            for r in review_items:
                rows += f"""
                <div style="padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.06); font-size:12px;">
                    <b>{r['applicant_label']}</b><br>
                    <span style="color:rgba(255,255,255,0.5);">Default risk {r['default']*100:.1f}%</span>
                </div>"""
            st.markdown(rows, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================================
# LOAN PREDICTION  (Module A)
# ==========================================================

def render_predict():
    st.markdown('<div class="hero-title">Loan prediction</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Applicant information — runs the ML model only. No AI explanation is generated here.</div>', unsafe_allow_html=True)

    with st.form("applicant_form"):
        cols = st.columns(3)
        for i, f in enumerate(APPLICANT_FIELDS):
            with cols[i % 3]:
                key = f"pf_{f['k']}"
                if f["type"] == "select":
                    idx = f["options"].index(f["default"]) if f["default"] in f["options"] else 0
                    st.selectbox(f["label"], f["options"], index=idx, key=key)
                else:
                    st.number_input(f["label"], value=float(f["default"]), step=float(f.get("step", 1)), key=key)
        submitted = st.form_submit_button("Predict Loan  →", type="primary")

    if submitted:
        applicant = {}
        for f in APPLICANT_FIELDS:
            val = st.session_state[f"pf_{f['k']}"]
            if f["k"] == "term":
                val = int(val)
            applicant[f["k"]] = val

        with st.spinner("Running the prediction model…"):
            try:
                data = api_post("/api/v1/decision", {
                    "applicant": applicant,
                    "question": "Summarize this applicant's decision.",
                    "session_id": st.session_state.session_id,
                })
                st.session_state.last_applicant = applicant
                st.session_state.last_prediction = data["prediction"]
                st.session_state.decision_chat = []
                st.session_state.prob_trend.append(data["prediction"]["repayment_probability"])
                st.session_state.history.insert(0, {
                    "type": "decision",
                    "applicant_label": f"Applicant · {applicant['sub_grade']}",
                    "sub_grade": applicant["sub_grade"],
                    "loan_amnt": applicant["loan_amnt"],
                    "prediction": data["prediction"]["prediction"],
                    "repayment": data["prediction"]["repayment_probability"],
                    "default": data["prediction"]["default_probability"],
                    "ts": time.time(),
                })
            except ApiError as e:
                st.error(f"Prediction failed: {e}")
                st.session_state.last_prediction = None

    if st.session_state.last_prediction:
        render_prediction_result(st.session_state.last_prediction)


def render_prediction_result(p):
    is_approved = p["prediction"] == "Approved"
    badge_color = "#34D399" if is_approved else "#F87171"
    confidence = max(p["repayment_probability"], p["default_probability"]) * 100

    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:rgba(255,255,255,0.5); margin-bottom:8px;">Decision</div>
            <div style="font-size:26px; font-weight:800; color:{badge_color}; margin-bottom:18px;">{p["prediction"]}</div>
            <div style="display:flex; gap:28px;">
                <div><div style="font-size:20px; font-weight:800;">{p["repayment_probability"]*100:.1f}%</div><div class="stat-lbl">Repayment</div></div>
                <div><div style="font-size:20px; font-weight:800;">{p["default_probability"]*100:.1f}%</div><div class="stat-lbl">Default risk</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:rgba(255,255,255,0.5); margin-bottom:10px;">Confidence</div>
            {donut_svg(confidence, badge_color)}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="light-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:700; font-size:14px; margin-bottom:14px;">Top risk drivers</div>', unsafe_allow_html=True)
    render_shap_bars(p.get("top_features", []), on_light=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.caption("This is the raw model output. Use the ✦ Ask AI button (bottom right) for an explanation, what-if analysis, or policy context.")


# ==========================================================
# KNOWLEDGE ASSISTANT  (Module B — standalone)
# ==========================================================

def render_knowledge():
    st.markdown('<div class="hero-title">Knowledge assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Standalone bank-policy Q&A — no connection to any prediction.</div>', unsafe_allow_html=True)

    st.markdown('<div class="light-card" style="max-width:800px;">', unsafe_allow_html=True)
    chip_cols = st.columns(3)
    chips = ["What is the maximum allowed DTI?", "What does Sub-Grade B3 mean?", "What are the conditions for a policy exception?"]
    for col, chip in zip(chip_cols, chips):
        with col:
            if st.button(chip, key=f"kb_chip_{chip[:10]}"):
                answer, sources = ask_knowledge(chip)
                st.session_state.kb_chat.append({"role": "user", "content": chip})
                st.session_state.kb_chat.append({"role": "assistant", "content": answer, "sources": sources})

    if not st.session_state.kb_chat:
        st.caption("Ask a question about Stratum Capital Bank's lending policy.")

    for msg in st.session_state.kb_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                st.markdown(" ".join(f'<span class="sc-source-chip">{s}</span>' for s in msg["sources"]), unsafe_allow_html=True)

    q = st.chat_input("e.g. What FICO range does Grade B require?", key="kb_chat_input")
    if q:
        answer, sources = ask_knowledge(q)
        st.session_state.kb_chat.append({"role": "user", "content": q})
        st.session_state.kb_chat.append({"role": "assistant", "content": answer, "sources": sources})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def ask_knowledge(question):
    try:
        data = api_post("/api/v1/knowledge", {"question": question, "session_id": st.session_state.session_id})
        sources = []
        for d in data.get("retrieved_documents", []):
            meta = d.get("document", {}).get("metadata", {})
            src = str(meta.get("source", "")).replace("\\", "/").split("/")[-1]
            page = meta.get("page_label", meta.get("page", "?"))
            sources.append(f"{src} · p.{page}")
        return data.get("answer", "No answer returned."), sources
    except ApiError as e:
        return f"Sorry — that request failed: {e}", []


# ==========================================================
# HISTORY
# ==========================================================

def render_history():
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown('<div class="hero-title">History</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Every application and AI conversation this session.</div>', unsafe_allow_html=True)
    with c2:
        if st.button("Clear session"):
            st.session_state.history = []
            st.rerun()

    st.markdown('<div class="light-card">', unsafe_allow_html=True)
    if not st.session_state.history:
        st.markdown('<div class="sc-empty on-light">Nothing recorded yet.</div>', unsafe_allow_html=True)
    else:
        rows = ""
        for h in st.session_state.history:
            if h["type"] == "decision":
                type_label, summary, result = "Prediction", h["applicant_label"], h["prediction"]
            else:
                meta = INTENT_META.get(h.get("intent"), INTENT_META["GENERAL"])
                type_label, summary, result = meta["label"], h.get("summary", "—"), "—"
            rows += f"""
            <tr>
                <td><span class="sc-pill sc-pill-pending">{type_label}</span></td>
                <td>{summary}</td>
                <td class="sc-muted">{result}</td>
                <td class="sc-muted">{time_ago(h["ts"])}</td>
            </tr>"""
        st.markdown(f"""
        <table class="sc-table">
            <thead><tr><th>Type</th><th>Summary</th><th>Result</th><th>When</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================================
# SETTINGS
# ==========================================================

def render_settings():
    st.markdown('<div class="hero-title">Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Configuration for this Streamlit session.</div>', unsafe_allow_html=True)

    st.markdown('<div class="light-card" style="max-width:560px;">', unsafe_allow_html=True)
    new_base = st.text_input("Backend API base URL", value=st.session_state.api_base)
    new_sid = st.text_input("Session ID", value=st.session_state.session_id)
    if st.button("Save & reconnect", type="primary"):
        st.session_state.api_base = new_base.rstrip("/")
        st.session_state.session_id = new_sid
        st.success("Settings saved.")
    st.markdown("""
    <p style="margin-top:14px; font-size:12px; color:#8B8F98;">
    Start the backend from the project root with:<br>
    <code style="background:#F5F6F8; padding:2px 6px; border-radius:5px;">uvicorn backend.main:app --reload --port 8000</code>
    </p>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================================
# MAIN
# ==========================================================

def main():
    st.set_page_config(page_title="Stratum · Credit Decision Console", layout="wide", page_icon="🛡")
    init_state()

    if not st.session_state.authenticated:
        render_login()
        return

    inject_css()
    render_sidebar()
    render_floating_ai_button()

    page = st.session_state.page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Loan Prediction":
        render_predict()
    elif page == "Knowledge Assistant":
        render_knowledge()
    elif page == "History":
        render_history()
    elif page == "Settings":
        render_settings()


if __name__ == "__main__":
    main()