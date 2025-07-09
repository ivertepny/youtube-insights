# streamlit_app.py
import streamlit as st
import requests
import pandas as pd

API_URL = "http://api:8000"
SEARCH_URL = f"{API_URL}/api/videos/search/"
LOGIN_URL = f"{API_URL}/api/users/login/"
REGISTER_URL = f"{API_URL}/api/users/register/"
LOGOUT_URL = f"{API_URL}/api/users/logout/"

st.set_page_config(page_title="YouTube Insights", layout="wide")

# 🔒 Hide Streamlit UI elements
st.markdown("""
    <style>
        #MainMenu, footer, header,
        .stDeployButton,
        button[title="Rerun"],
        button[title="View app settings"],
        [data-testid="stDeploymentIndicator"],
        [data-testid="stStatusWidget"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Session Initialization ---
if "access" not in st.session_state:
    st.session_state.access = None
if "refresh" not in st.session_state:
    st.session_state.refresh = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "df_display" not in st.session_state:
    st.session_state.df_display = None
if "Navigation" not in st.session_state:
    st.session_state["Navigation"] = "Login"

# --- Auth Navigation ---
page = st.sidebar.selectbox(
    "Navigation",
    ["Login", "Register", "Main App", "Logout"],
    index=["Login", "Register", "Main App", "Logout"].index(st.session_state["Navigation"])
)

# --- Register Page ---
if page == "Register":
    st.title("📝 Register")
    with st.form("register_form"):
        email = st.text_input("Email")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register")

    if submitted:
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        }
        res = requests.post(REGISTER_URL, json=payload)
        if res.status_code == 201:
            st.toast("✅ Registration successful. Redirecting to login...", icon="✅")
            st.session_state["Navigation"] = "Login"
            st.rerun()
        else:
            st.error(f"❌ Registration failed: {res.json()}")

# --- Login Page ---
elif page == "Login":
    st.title("🔐 Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        payload = {"email": email, "password": password}
        res = requests.post(LOGIN_URL, json=payload)
        if res.status_code == 200:
            data = res.json()
            st.session_state.access = data["token"]["access"]
            st.session_state.refresh = data["token"]["refresh"]
            st.session_state.user_email = data["user"]["email"]
            st.toast("✅ Login successful. Redirecting...", icon="🔓")
            st.session_state["Navigation"] = "Main App"
            st.rerun()
        else:
            st.error(f"❌ Login failed: {res.json()}")

# --- Logout Page ---
elif page == "Logout":
    st.title("🚪 Logout")
    if st.session_state.refresh:
        res = requests.post(LOGOUT_URL, json={"refresh": st.session_state.refresh},
                            headers={"Authorization": f"Bearer {st.session_state.access}"})
        if res.status_code in [200, 205]:
            st.toast("✅ Logged out successfully.", icon="🚪")
        else:
            st.error(f"❌ Logout failed: {res.json()}")
    else:
        st.warning("⚠️ You are not logged in.")

    # Clear session and redirect to login
    st.session_state.access = None
    st.session_state.refresh = None
    st.session_state.user_email = None
    st.session_state.df_display = None
    st.session_state["Navigation"] = "Login"
    st.rerun()

# --- Main App Page ---
elif page == "Main App":
    st.title("📊 YouTube Hidden Gems Finder")

    if not st.session_state.access:
        st.warning("⚠️ You must be logged in to use this feature.")
        st.stop()

    query = st.text_input("🔍 Search Query", value="ai")
    max_results = st.slider("🎯 Max Results", 5, 50, 20)
    published_after = st.date_input("📅 Published After (optional)")
    category_id = st.text_input("🎞️ Video Category ID (optional)", value="")

    if st.button("Search"):
        params = {
            "q": query,
            "max_results": max_results,
        }
        if published_after:
            params["published_after"] = published_after.isoformat() + "T00:00:00Z"
        if category_id:
            params["video_category_id"] = category_id

        with st.spinner("🔎 Fetching results..."):
            try:
                response = requests.get(SEARCH_URL, params=params)
                response.raise_for_status()
                data = response.json()
                if not data:
                    st.warning("⚠️ No results found.")
                    st.session_state.df_display = None
                else:
                    df = pd.DataFrame(data)
                    required = ["title", "channel_title", "views", "subs", "score", "insight", "video_id"]
                    if not all(col in df.columns for col in required):
                        st.error("❌ Some expected fields are missing.")
                        st.dataframe(df)
                        st.session_state.df_display = None
                    else:
                        df["video_link"] = "https://www.youtube.com/watch?v=" + df["video_id"]
                        df_display = df[["title", "channel_title", "views", "subs", "score", "insight", "video_link"]]
                        df_display = df_display.rename(columns={"video_link": "🔗 Link"})
                        st.session_state.df_display = df_display
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {e}")
                st.session_state.df_display = None

    if st.session_state.df_display is not None:
        st.dataframe(st.session_state.df_display)
        csv = st.session_state.df_display.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv, "youtube_insights.csv", "text/csv")
