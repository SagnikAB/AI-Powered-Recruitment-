import sqlite3

DB = "database.db"


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        score INTEGER,
        rank TEXT,
        keywords TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_resume(filename, score, keywords, rank):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO resumes (filename, score, rank, keywords)
    VALUES (?, ?, ?, ?)
    """, (filename, score, rank, ", ".join(keywords)))

    conn.commit()
    conn.close()


def get_all_resumes():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM resumes ORDER BY id DESC")
    data = c.fetchall()

    conn.close()
    return data