import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import sqlite3
import os
import pandas as pd

from recommender import HybridRecommender
from database import get_connection, create_tables

# =============================
# TMDB API KEY
# =============================
API_KEY = os.getenv("TMDB_API_KEY")

if API_KEY is None:
    raise ValueError("TMDB_API_KEY is not set in environment variables")

# =============================
# INIT DATABASE
# =============================
create_tables()

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
# LOAD RECOMMENDER MODEL
# =============================
movie_matrix = pd.read_csv("movie_matrix.csv", index_col=0)
ratings_count = pd.read_csv("ratings_count.csv", index_col=0)
movies = pd.read_csv("movies.csv")

recommender = HybridRecommender(
    movie_matrix,
    ratings_count,
    movies
)

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
# SAVE HISTORY
# =============================
def save_history(username, movie):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO history (username, movie) VALUES (?, ?)",
        (username, movie)
    )

    conn.commit()
    conn.close()

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

        with st.spinner("Finding best movies..."):

            try:
                data = recommender.recommend(movie_name, top_n)

                if "error" in data:
                    st.error(data["error"])

                else:
                    st.success(f"Recommendations for: {data['input_movie']}")

                    save_history(username, data["input_movie"])

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

            except Exception as e:
                st.error(f"Error: {e}")

# =============================
# TAB 2 - TRENDING
# =============================
with tab2:

    st.subheader("🔥 Trending Movies (Live from TMDb)")

    try:
        url = (
            f"https://api.themoviedb.org/3/trending/movie/day"
            f"?api_key={API_KEY}"
        )

        r = requests.get(url, timeout=10)
        data = r.json()

        movies_data = []

        for m in data.get("results", []):
            movies_data.append({
                "title": m.get("title"),
                "rating": m.get("vote_average"),
                "poster": (
                    "https://image.tmdb.org/t/p/w500" + m["poster_path"]
                    if m.get("poster_path") else None
                )
            })

        cols = st.columns(5)

        for idx, movie in enumerate(movies_data):

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
        conn = get_connection()
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