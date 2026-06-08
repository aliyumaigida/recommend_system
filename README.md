# 🎬 AI Movie Recommendation System

An AI-powered Movie Recommendation System built with Python and Streamlit that provides personalized movie
recommendations based on user preferences and rating patterns.

## 🚀 Live Demo

https://recommendsystem-nkjtydk663wd2uuvb6fzrn.streamlit.app/

## 📌 Features

* Personalized movie recommendations
* User registration and login system
* Secure password hashing
* Recommendation history tracking
* Movie poster integration using TMDB API
* Movie trailer integration using TMDB API
* Trending movies section
* Interactive and responsive Streamlit interface
* Cloud deployment

## 🛠️ Technologies Used

* Python
* Pandas
* Streamlit
* SQLite
* Machine Learning
* TMDB API

## 🤖 Recommendation Technique

The recommendation engine uses collaborative filtering techniques to identify movies with similar user rating patterns and generate personalized recommendations.

## 📂 Project Structure

```text
├── app.py
├── recommender.py
├── database.py
├── movies.csv
├── movie_matrix.csv
├── ratings_count.csv
├── requirements.txt
└── README.md
```

## ⚙️ Installation

1. Clone the repository

```bash
git clone <repository-url>
```

2. Navigate to the project folder

```bash
cd movie-recommendation-system
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set your TMDB API key

```bash
TMDB_API_KEY=your_api_key
```

5. Run the application

```bash
streamlit run app.py
```

## 📈 Future Improvements

* PostgreSQL database integration
* Advanced recommendation algorithms (Cosine Similarity, SVD)
* User profile management
* Movie ratings and reviews
* Better recommendation personalization

## 👨‍💻 Author

Aliyu Maigida

If you find this project useful, feel free to star the repository.
