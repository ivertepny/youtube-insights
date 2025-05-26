# streamlit_app.py
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="YouTube Insights", layout="wide")

# 🔒 Приховати Deploy, Rerun, Settings
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        button[title="Rerun"] {display: none;}
        button[title="View app settings"] {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("📊 YouTube Hidden Gems Finder")

API_URL = "http://api:8000/api/videos/search/"

query = st.text_input("🔍 Search Query", value="ai")
max_results = st.slider("🎯 Max Results", 5, 50, 20)
published_after = st.date_input("📅 Published After (optional)")
category_id = st.text_input("🎞️ Video Category ID (optional)", value="")

# Ініціалізуємо session_state для зберігання результатів, якщо його немає
if "df_display" not in st.session_state:
    st.session_state.df_display = None

# Кнопка пошуку — робимо запит і зберігаємо результат у сесії
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
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                st.error("❌ Failed to decode JSON. Response might be empty or malformed.")
                st.text(response.text)
                st.stop()

            if not data:
                st.warning("⚠️ No results found.")
                st.session_state.df_display = None
            else:
                df = pd.DataFrame(data)
                required_cols = ["title", "channel_title", "views", "subs", "score", "insight", "video_id"]
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    st.error(f"❌ Missing expected columns in response: {missing_cols}")
                    st.dataframe(df)  # show raw result for debugging
                    st.session_state.df_display = None
                else:
                    df["video_link"] = "https://www.youtube.com/watch?v=" + df["video_id"]
                    df_display = df[["title", "channel_title", "views", "subs", "score", "insight", "video_link"]]
                    df_display = df_display.rename(columns={"video_link": "🔗 Link"})
                    st.session_state.df_display = df_display
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Request failed: {e}")
            st.session_state.df_display = None

# Відображаємо збережений результат, якщо він є
if st.session_state.df_display is not None:
    st.dataframe(st.session_state.df_display)
    csv = st.session_state.df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name='youtube_insights.csv',
        mime='text/csv',
    )
