from fastapi import FastAPI, HTTPException
import pandas as pd
import requests

from recommender import HybridRecommender
from database import get_connection
import os

app = FastAPI(title="Movie Recommendation API 🚀")



API_KEY = os.getenv("TMDB_API_KEY")

# -------------------------
# SAVE HISTORY
# -------------------------
def save_history(username, movie):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO history (username, movie) VALUES (?, ?)",
        (username, movie)
    )

    conn.commit()
    conn.close()

# -------------------------
# LOAD DATA SAFELY
# -------------------------
try:
    movie_matrix = pd.read_csv("movie_matrix.csv", index_col=0)
    ratings_count = pd.read_csv("ratings_count.csv", index_col=0)
    movies = pd.read_csv("movies.csv")

except Exception as e:
    raise RuntimeError(f"Failed to load data: {e}")

# -------------------------
# INIT MODEL
# -------------------------
try:
    recommender = HybridRecommender(
        movie_matrix,
        ratings_count,
        movies
    )
except Exception as e:
    raise RuntimeError(f"Model initialization failed: {e}")

# -------------------------
# HOME ROUTE
# -------------------------
@app.get("/")
def home():
    return {"message": "API running 🚀"}

# -------------------------
# YOUR RECOMMENDER ENDPOINT
# -------------------------
@app.get("/recommend")
def recommend(movie: str, top_n: int = 10, username: str = "guest"):

    if not movie or movie.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Movie cannot be empty"
        )

    result = recommender.recommend(movie, top_n)

    if "error" in result:
        return result

    save_history(username, result["input_movie"])

    return result

# -------------------------
# 🔥 NEW: REAL-TIME TRENDING (TMDB)
# -------------------------
@app.get("/trending")
def trending():

    url = (
        f"https://api.themoviedb.org/3/trending/movie/day"
        f"?api_key={API_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        movies = []

        for m in data.get("results", []):
            movies.append({
                "title": m.get("title"),
                "rating": m.get("vote_average"),
                "popularity": m.get("popularity"),
                "poster": (
                    "https://image.tmdb.org/t/p/w500"
                    + m["poster_path"]
                    if m.get("poster_path") else None
                )
            })

        return {
            "source": "TMDb Live Trending",
            "results": movies
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trending movies: {str(e)}"
        )

# -------------------------
# 🔥 NEW: SIMILAR MOVIES (TMDB REAL-TIME)
# -------------------------
@app.get("/similar/{movie_id}")
def similar(movie_id: int):

    url = (
        f"https://api.themoviedb.org/3/movie/"
        f"{movie_id}/similar?api_key={API_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        results = []

        for m in data.get("results", []):
            results.append({
                "title": m.get("title"),
                "rating": m.get("vote_average"),
                "poster": (
                    "https://image.tmdb.org/t/p/w500"
                    + m["poster_path"]
                    if m.get("poster_path") else None
                )
            })

        return {
            "source": "TMDb Similar Movies",
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch similar movies: {str(e)}"
        )
    


# uvicorn main:app --reload
# streamlit run app.py    