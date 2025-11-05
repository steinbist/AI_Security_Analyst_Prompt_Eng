from __future__ import annotations
import os, textwrap, json
import requests
import streamlit as st

st.set_page_config(page_title="AI Security Analyst Assistant", layout="wide")

# ---------------- Session State ----------------
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "api_base" not in st.session_state:
    st.session_state.api_base = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def get_api_base() -> str:
    return st.session_state.api_base.rstrip("/")

# ---------------- Utilities ----------------
def _errbox(title: str, detail: str):
    with st.expander(f"⚠️ {title}", expanded=True):
        st.code(detail)

def auth_headers():
    t = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {t}"} if t else {}

# ---------------- Login View ----------------
def show_login():
    st.title("🔐 AI Security Analyst Assistant — Login")

    with st.form("login_form", clear_on_submit=False):
        # API base is editable here so it exists before auth and sidebar rendering
        st.session_state.api_base = st.text_input(
            "API Base URL",
            value=st.session_state.api_base,
            help="Your FastAPI server root (e.g., http://127.0.0.1:8000)",
        )
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")

    if submitted:
        api_base = get_api_base()
        try:
            r = requests.post(
                f"{api_base}/auth/login",
                json={"username": username, "password": password},
                timeout=20,
            )
            if r.ok:
                tokens = r.json()
                st.session_state.is_authenticated = True
                st.session_state.username = username
                st.session_state.access_token = tokens["access_token"]
                st.session_state.refresh_token = tokens["refresh_token"]
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
                try:
                    _errbox("Server response", r.text)
                except Exception:
                    pass
        except Exception as ex:
            st.error(f"Login failed: {ex}")

# ---------------- Gate: only show app after auth ----------------
if not st.session_state.is_authenticated:
    show_login()
    st.stop()

# ---------------- Authenticated UI ----------------
# Sidebar shows only after login
st.sidebar.success(f"Logged in as: {st.session_state.username}")
def _logout():
    st.session_state.update(
        {
            "is_authenticated": False,
            "username": None,
            "access_token": None,
            "refresh_token": None,
        }
    )
st.sidebar.button("Logout", on_click=_logout)

# Server controls (read-only api_base, but you can make it editable if you prefer)
st.sidebar.header("Server")
st.sidebar.text_input(
    "API Base URL",
    value=st.session_state.api_base,
    key="api_base_readonly",
    disabled=True,
)
if st.sidebar.button("Check Health"):
    try:
        r = requests.get(f"{get_api_base()}/health", timeout=10)
        st.sidebar.json(r.json())
    except Exception as ex:
        _errbox("Health check failed", f"{type(ex).__name__}: {ex}")

st.sidebar.header("Output")
output_format = st.sidebar.radio("Format", ["json", "markdown"], index=0)
schema = st.sidebar.selectbox(
    "Schema", ["risk_assessment", "event_summary", "policy_alignment"], index=0
)

st.sidebar.header("Context")
time_window = st.sidebar.text_input("Time window (optional)", value="Not specified")
inputs_selected = st.sidebar.multiselect(
    "Inputs", ["logs", "access_records", "policy_text"], default=["logs", "access_records", "policy_text"]
)

# ----- Main: input & action -----
st.title("🔐 AI Security Analyst Assistant")
# sample = textwrap.dedent(
#     """\
#     Access denied for UserID 4219 at Gate 4
#     Last successful login: 2025-10-31
#     User clearance: Secret
#     Facility requirement: Top Secret
# """
# )
txt = st.text_area("Paste logs / access records / policies", textwrap.dedent(), height=180)

if st.button("Analyze", type="primary"):
    api_base = get_api_base()
    body = {
        "input_text": txt,
        "output_format": output_format,
        "schema": schema,
        "time_window": (time_window or None),
        "inputs": inputs_selected or None,
    }
    try:
        r = requests.post(
            f"{api_base}/analyze", headers=auth_headers(), json=body, timeout=60
        )
        st.write(f"HTTP {r.status_code}")
        ct = r.headers.get("content-type", "")
        if "json" in ct:
            data = r.json()
            st.json(data)
            # Simple findings table for risk_assessment
            if isinstance(data, dict) and data.get("data", {}).get("type") == "risk_assessment":
                rows = []
                for f in data["data"].get("findings", []):
                    rows.append(
                        {
                            "ID": f.get("id"),
                            "Title": f.get("title"),
                            "Severity": f.get("severity"),
                            "Score": f.get("risk_score"),
                            "Confidence": f.get("confidence"),
                        }
                    )
                if rows:
                    st.dataframe(rows, use_container_width=True)
        else:
            st.text(r.text[:4000])
    except Exception as ex:
        _errbox("Analyze failed", f"{type(ex).__name__}: {ex}")
