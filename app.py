from streamlit_autorefresh import st_autorefresh
import streamlit as st
import requests
import sqlite3

# -----------------------------
# TMDb API KEY
# -----------------------------

import os

API_KEY = os.getenv("TMDB_API_KEY")

if API_KEY is None:
    raise ValueError("TMDB_API_KEY is not set in environment variables")

# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Movie Recommendation System")
st.write("Get personalized movie recommendations instantly.")

# =============================
# AUTO REFRESH TRENDING
# =============================
st_autorefresh(interval=60000, key="trending_refresh")

# =============================
# USER INPUT
# =============================
username = st.text_input("Enter Username", value="guest")

if "selected_movie" not in st.session_state:
    st.session_state["selected_movie"] = ""

movie_name = st.text_input(
    "Enter Movie Name",
    value=st.session_state["selected_movie"],
    placeholder="e.g Star Wars"
)

top_n = st.slider("Number of Recommendations", 1, 20, 10)

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🎬 Recommended", "🔥 Trending", "📜 History"])

# =============================
# FETCH POSTER
# =============================
def fetch_poster(movie_name):

    clean_name = movie_name.split("(")[0].strip()

    url = (
        f"https://api.themoviedb.org/3/search/movie"
        f"?api_key={API_KEY}&query={clean_name}"
    )

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        if data.get("results"):
            poster_path = data["results"][0].get("poster_path")

            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path

    except:
        return None

    return None

# =============================
# FETCH TRAILER
# =============================
def fetch_trailer(movie_name):

    clean_name = movie_name.split("(")[0].strip()

    url = (
        f"https://api.themoviedb.org/3/search/movie"
        f"?api_key={API_KEY}&query={clean_name}"
    )

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        if data.get("results"):

            movie_id = data["results"][0]["id"]

            trailer_url = (
                f"https://api.themoviedb.org/3/movie/"
                f"{movie_id}/videos?api_key={API_KEY}"
            )

            tr = requests.get(trailer_url)
            trailer_data = tr.json()

            for v in trailer_data.get("results", []):
                if v["type"] == "Trailer":
                    return "https://www.youtube.com/embed/" + v["key"]

    except:
        return None

    return None

# =============================
# TAB 1 - RECOMMENDED
# =============================
with tab1:

    if movie_name:

        url = "http://127.0.0.1:8000/recommend"

        params = {
            "movie": movie_name,
            "top_n": top_n,
            "username": username
        }

        with st.spinner("Finding best movies..."):

            try:
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

            except:
                st.error("FastAPI server not running.")
                st.stop()

        if "error" in data:
            st.error(data["error"])

        else:
            st.success(f"Recommendations for: {data['input_movie']}")

            cols = st.columns(5)

            for idx, movie in enumerate(data["recommendations"]):

                with cols[idx % 5]:

                    poster = fetch_poster(movie["movie"])

                    if poster:
                        st.image(poster, use_container_width=True)
                    else:
                        st.text("No poster")

                    if st.button(movie["movie"], key=f"rec_{idx}"):

                        st.session_state["selected_movie"] = movie["movie"]
                        st.rerun()

                    st.metric("Score", round(movie["score"], 3))
                    st.metric("Ratings", movie["ratings"])

                    trailer = fetch_trailer(movie["movie"])

                    if trailer:
                        with st.expander("🎥 Trailer"):
                            st.video(trailer)

# =============================
# TAB 2 - TRENDING (AUTO LIVE)
# =============================
with tab2:

    st.subheader("🔥 Trending Movies (Live from TMDb)")

    try:
        r = requests.get("http://127.0.0.1:8000/trending", timeout=10)
        data = r.json()

        cols = st.columns(5)

        for idx, movie in enumerate(data["results"]):

            with cols[idx % 5]:

                if movie["poster"]:
                    st.image(movie["poster"], use_container_width=True)

                st.write(movie["title"])
                st.write("⭐", movie["rating"])

    except:
        st.warning("Loading trending movies...")

# =============================
# TAB 3 - HISTORY
# =============================
with tab3:

    st.subheader("📜 Your Watch History")

    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT movie FROM history WHERE username=?",
            (username,)
        )

        rows = cursor.fetchall()
        conn.close()

        if rows:
            for r in rows:
                st.write("🎬", r[0])
        else:
            st.info("No history found.")

    except:
        st.error("Database error or table missing.")