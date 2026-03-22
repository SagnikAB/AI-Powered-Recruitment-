import sqlite3
import os
import hashlib
import secrets

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "resumes.db")

# ── Init ──────────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sessions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Resumes table (now with user_id + job_description)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER,
            name            TEXT,
            score           INTEGER,
            matched         TEXT,
            missing         TEXT,
            rank            TEXT,
            job_description TEXT,
            recommendations TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ── Auth helpers ──────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, email: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username.strip(), email.strip().lower(), hash_password(password))
        )
        conn.commit()
        user_id = cur.lastrowid
        return {"success": True, "user_id": user_id}
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return {"success": False, "error": "Username already taken"}
        return {"success": False, "error": "Email already registered"}
    finally:
        conn.close()

def login_user(email: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username FROM users WHERE email=? AND password=?",
        (email.strip().lower(), hash_password(password))
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"success": False, "error": "Invalid email or password"}
    token = secrets.token_hex(32)
    _create_session(row[0], token)
    return {"success": True, "token": token, "username": row[1], "user_id": row[0]}

def _create_session(user_id: int, token: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    conn.close()

def get_user_from_token(token: str):
    if not token:
        return None
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT u.id, u.username FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.token=?",
        (token,)
    )
    row = cur.fetchone()
    conn.close()
    return {"id": row[0], "username": row[1]} if row else None

def logout_user(token: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token=?", (token,))
    conn.commit()
    conn.close()


# ── Resume helpers ────────────────────────────────────────────────────────────
def save_resume(user_id, name, score, matched, missing, rank, job_description, recommendations):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO resumes
           (user_id, name, score, matched, missing, rank, job_description, recommendations)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            name,
            score,
            ", ".join(matched) if isinstance(matched, list) else matched,
            ", ".join(missing) if isinstance(missing, list) else missing,
            rank,
            job_description or "",
            ", ".join(recommendations) if isinstance(recommendations, list) else recommendations,
        )
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def get_all_resumes(user_id=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if user_id:
        cur.execute(
            "SELECT id,name,score,matched,missing,rank,job_description,recommendations,created_at FROM resumes WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        )
    else:
        cur.execute(
            "SELECT id,name,score,matched,missing,rank,job_description,recommendations,created_at FROM resumes ORDER BY id DESC"
        )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "name": r[1], "score": r[2],
            "matched": r[3], "missing": r[4], "rank": r[5],
            "job_description": r[6], "recommendations": r[7], "date": r[8]
        }
        for r in rows
    ]

def get_resume_by_id(resume_id: int, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if user_id:
        cur.execute(
            "SELECT id,name,score,matched,missing,rank,job_description,recommendations,created_at FROM resumes WHERE id=? AND user_id=?",
            (resume_id, user_id)
        )
    else:
        cur.execute(
            "SELECT id,name,score,matched,missing,rank,job_description,recommendations,created_at FROM resumes WHERE id=?",
            (resume_id,)
        )
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r[0], "name": r[1], "score": r[2],
        "matched": r[3], "missing": r[4], "rank": r[5],
        "job_description": r[6], "recommendations": r[7], "date": r[8]
    }