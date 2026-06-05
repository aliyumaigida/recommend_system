import sqlite3

def get_connection():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # HISTORY TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        movie TEXT
    )
    """)

    conn.commit()
    conn.close()


create_tables()
