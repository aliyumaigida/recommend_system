from fuzzywuzzy import process
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class HybridRecommender:

    def __init__(self, movie_matrix, ratings_count, movies_df=None):

        self.movie_matrix = movie_matrix.copy()
        self.ratings_count = ratings_count.copy()

        # -----------------------------
        # CLEAN COLUMN NAMES
        # -----------------------------
        self.movie_matrix.columns = [
            str(col).lower().strip()
            for col in self.movie_matrix.columns
        ]

        self.ratings_count.index = [
            str(idx).lower().strip()
            for idx in self.ratings_count.index
        ]

        # -----------------------------
        # REMOVE BAD MOVIES
        # -----------------------------
        bad_movies = {"unknown", "nan", "none", ""}

        self.movie_matrix = self.movie_matrix[
            [col for col in self.movie_matrix.columns if col not in bad_movies]
        ]

        # -----------------------------
        # FILL MISSING VALUES
        # -----------------------------
        self.filled_matrix = self.movie_matrix.fillna(0)

        # -----------------------------
        # NORMALIZE (IMPORTANT UPGRADE)
        # reduces popularity bias
        # -----------------------------
        self.filled_matrix = self.filled_matrix.apply(
            lambda x: x - x.mean(),
            axis=0
        )

    # -------------------------------------------------
    # MAIN RECOMMENDER
    # -------------------------------------------------
    def recommend(self, movie_name, top_n=10):

        movie_name = str(movie_name).lower().strip()

        movies = list(self.movie_matrix.columns)

        # -----------------------------
        # FUZZY MATCH
        # -----------------------------
        match = process.extractOne(
            movie_name,
            movies,
            score_cutoff=60
        )

        if not match:
            return {
                "error": "Movie not found",
                "hint": "Try popular movies like Star Wars, Titanic, Toy Story"
            }

        best_match = match[0]

        # -----------------------------
        # TARGET VECTOR
        # -----------------------------
        target_vector = self.filled_matrix[best_match].values.reshape(1, -1)

        similarities = {}

        # -----------------------------
        # COSINE SIMILARITY LOOP
        # -----------------------------
        for movie in movies:

            if movie == best_match:
                continue

            movie_vector = self.filled_matrix[movie].values.reshape(1, -1)

            score = cosine_similarity(
                target_vector,
                movie_vector
            )[0][0]

            # keep only meaningful similarity
            if np.isfinite(score) and score > 0:
                similarities[movie] = score

        # -----------------------------
        # NO RESULTS SAFETY CHECK
        # -----------------------------
        if not similarities:
            return {
                "error": "No recommendations found",
                "hint": "Try another popular movie"
            }

        # -----------------------------
        # DATAFRAME
        # -----------------------------
        df = pd.DataFrame.from_dict(
            similarities,
            orient="index",
            columns=["score"]
        )

        # -----------------------------
        # ADD RATINGS COUNT (SAFE JOIN)
        # -----------------------------
        df["num_of_ratings"] = self.ratings_count["num_of_ratings"].reindex(df.index)
        df["num_of_ratings"] = df["num_of_ratings"].fillna(0).astype(int)

        # -----------------------------
        # FILTER LOW QUALITY MOVIES
        # -----------------------------
        df = df[df["num_of_ratings"] >= 10]

        # fallback if too strict
        if df.empty:
            df = pd.DataFrame.from_dict(
                similarities,
                orient="index",
                columns=["score"]
            )
            df["num_of_ratings"] = self.ratings_count["num_of_ratings"].reindex(df.index)
            df["num_of_ratings"] = df["num_of_ratings"].fillna(0).astype(int)

        # -----------------------------
        # SORT RESULTS
        # -----------------------------
        df = df.sort_values(by="score", ascending=False).head(top_n)

        # -----------------------------
        # OUTPUT
        # -----------------------------
        return {
            "input_movie": best_match,
            "recommendations": [
                {
                    "movie": movie,
                    "score": round(float(row["score"]), 3),
                    "ratings": int(row["num_of_ratings"])
                }
                for movie, row in df.iterrows()
            ]
        }