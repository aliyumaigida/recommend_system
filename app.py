import streamlit as st
import requests
import pandas as pd
import os
import hashlib

from recommender import HybridRecommender
from database import get_connection, create_tables

# =============================
# TMDB API KEY
# =============================
API_KEY = os.getenv("TMDB_API_KEY")

if not API_KEY:
    raise ValueError("TMDB_API_KEY is not set")

# =============================
# INIT DB
# =============================
create_tables()

# =============================
# PASSWORD HASH
# =============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Movie Recommendation System")

# =============================
# LOAD MODEL
# =============================
movie_matrix = pd.read_csv("movie_matrix.csv", index_col=0)
ratings_count = pd.read_csv("ratings_count.csv", index_col=0)
movies = pd.read_csv("movies.csv")

recommender = HybridRecommender(movie_matrix, ratings_count, movies)

# =============================
# SESSION STATE INIT
# =============================
if "user" not in st.session_state:
    st.session_state.user = None

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = "Star Wars"

# IMPORTANT: protect session stability
user_logged_in = st.session_state.user is not None

# =============================
# SELECT MOVIE FUNCTION (NO RERUN BUG)
# =============================
def select_movie(movie):
    st.session_state.selected_movie = movie

# =============================
# SIDEBAR
# =============================
st.sidebar.title("🔐 Account System")

if user_logged_in:
    st.sidebar.success(f"👤 {st.session_state.user}")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.selected_movie = "Star Wars"
        st.rerun()

else:
    menu = st.sidebar.radio("Menu", ["Login", "Register"])

    # ---------------- REGISTER ----------------
    if menu == "Register":
        new_user = st.text_input("Username", key="reg_user").lower().strip()
        new_pass = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Register"):
            conn = get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (new_user, hash_password(new_pass))
                )
                conn.commit()
                st.success("Account created successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

            conn.close()

    # ---------------- LOGIN ----------------
    if menu == "Login":
        username = st.text_input("Username", key="login_user").lower().strip()
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT password FROM users WHERE username=?",
                (username,)
            )

            result = cursor.fetchone()
            conn.close()

            if result and result[0] == hash_password(password):
                st.session_state.user = username
                st.success(f"Welcome {username} 🎉")
                st.rerun()
            else:
                st.error("Invalid credentials")

# =============================
# STOP IF NOT LOGGED IN
# =============================
if st.session_state.user is None:
    st.stop()

username = st.session_state.user

# =============================
# INPUT
# =============================
movie_name = st.text_input(
    "Enter Movie Name",
    value=st.session_state.selected_movie
)

top_n = st.slider("Number of Recommendations", 1, 20, 10)

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
# POSTER
# =============================
def fetch_poster(movie_name):
    clean = movie_name.split("(")[0].strip()

    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={clean}"

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        if data.get("results"):
            poster = data["results"][0].get("poster_path")
            if poster:
                return "https://image.tmdb.org/t/p/w500" + poster
    except:
        return None

    return None

# =============================
# TRAILER
# =============================
def fetch_trailer(movie_name):
    clean = movie_name.split("(")[0].strip()

    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={clean}"

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        if data.get("results"):
            movie_id = data["results"][0]["id"]

            t_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}"
            tr = requests.get(t_url)
            tdata = tr.json()

            for v in tdata.get("results", []):
                if v["type"] == "Trailer" and v["site"] == "YouTube":
                    return "https://www.youtube.com/watch?v=" + v["key"]
    except:
        return None

    return None

# =============================
# TAB 1 - RECOMMEND
# =============================
with tab1:

    if st.button("Get Recommendations"):

        data = recommender.recommend(movie_name, top_n)

        if "error" in data:
            st.error(data["error"])
        else:
            st.success(f"Results for: {data['input_movie']}")

            save_history(username, data["input_movie"])

            cols = st.columns(5)

            for i, movie in enumerate(data["recommendations"]):

                with cols[i % 5]:

                    # CLICK MOVIE → NEW SEARCH (FIXED)
                    st.button(
                        movie["movie"],
                        key=f"movie_{i}",
                        on_click=select_movie,
                        args=(movie["movie"],)
                    )

                    poster = fetch_poster(movie["movie"])
                    if poster:
                        st.image(poster)

                    st.metric("Score", movie["score"])
                    st.metric("Ratings", movie["ratings"])

                    trailer = fetch_trailer(movie["movie"])
                    if trailer:
                        with st.expander("🎥 Trailer"):
                            st.video(trailer)

# =============================
# TAB 2 - TRENDING
# =============================
with tab2:

    st.subheader("🔥 Trending Movies")

    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={API_KEY}"
    r = requests.get(url)
    data = r.json()

    cols = st.columns(5)

    for i, m in enumerate(data.get("results", [])):

        with cols[i % 5]:
            if m.get("poster_path"):
                st.image("https://image.tmdb.org/t/p/w500" + m["poster_path"])
            st.write(m.get("title"))
            st.write("⭐", m.get("vote_average"))

# =============================
# TAB 3 - HISTORY
# =============================
with tab3:

    st.subheader("📜 Your Watch History")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT movie FROM history WHERE username=?",
        (username,)
    )

    rows = cursor.fetchall()
    conn.close()

    if rows:
        for r in rows[::-1]:
            st.write("🎬", r[0])
    else:
        st.info("No history found.")
