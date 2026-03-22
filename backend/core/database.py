import sqlite3

def init_db():
    conn = sqlite3.connect("resumes.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY,
        name TEXT,
        score INTEGER,
        rank TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_resume(name, score, rank):
    conn = sqlite3.connect("resumes.db")
    cur = conn.cursor()

    cur.execute("INSERT INTO resumes (name, score, rank) VALUES (?, ?, ?)",
                (name, score, rank))

    conn.commit()
    conn.close()

def get_all_resumes():
    conn = sqlite3.connect("resumes.db")
    cur = conn.cursor()

    cur.execute("SELECT name, score, rank FROM resumes")
    data = cur.fetchall()

    conn.close()

    return [{"name": d[0], "score": d[1], "rank": d[2]} for d in data]