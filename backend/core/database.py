import sqlite3
import os
import hashlib
import secrets
import json

DB_PATH = os.getenv("DB_PATH", "resumes.db")

# ── Init ──────────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

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

    # Interview sessions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER,
            resume_id       INTEGER,
            questions       TEXT,
            answers         TEXT,
            results         TEXT,
            overall_score   INTEGER,
            level           TEXT,
            job_suggestions TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id)   REFERENCES users(id),
            FOREIGN KEY(resume_id) REFERENCES resumes(id)
        )
    """)

    _ensure_column(cur, "resumes", "user_id", "INTEGER")
    _ensure_column(cur, "resumes", "missing", "TEXT DEFAULT ''")
    _ensure_column(cur, "resumes", "job_description", "TEXT DEFAULT ''")
    _ensure_column(cur, "resumes", "recommendations", "TEXT DEFAULT ''")

    conn.commit()
    conn.close()


# ── Auth ──────────────────────────────────────────────────────────────────────

def _ensure_column(cur, table, column, definition):
    cur.execute(f"PRAGMA table_info({table})")
    columns = {row[1] for row in cur.fetchall()}
    if column not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

def register_user(username, email, password):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username.strip(), email.strip().lower(), hash_password(password))
        )
        conn.commit()
        return {"success": True, "user_id": cur.lastrowid}
    except sqlite3.IntegrityError as e:
        return {"success": False, "error": "Username already taken" if "username" in str(e) else "Email already registered"}
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
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

def _create_session(user_id, token):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    conn.close()

def get_user_from_token(token):
    if not token:
        return None
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "SELECT u.id, u.username FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.token=?",
        (token,)
    )
    row = cur.fetchone()
    conn.close()
    return {"id": row[0], "username": row[1]} if row else None

def logout_user(token):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token=?", (token,))
    conn.commit()
    conn.close()


# ── Resumes ───────────────────────────────────────────────────────────────────
def save_resume(user_id, name, score, matched, missing, rank, job_description, recommendations):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        """INSERT INTO resumes
           (user_id,name,score,matched,missing,rank,job_description,recommendations)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            user_id, name, score,
            ", ".join(matched) if isinstance(matched, list) else matched,
            ", ".join(missing) if isinstance(missing, list) else missing,
            rank, job_description or "",
            ", ".join(recommendations) if isinstance(recommendations, list) else recommendations,
        )
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def get_all_resumes(user_id=None):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
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
    return [{"id":r[0],"name":r[1],"score":r[2],"matched":r[3],"missing":r[4],
             "rank":r[5],"job_description":r[6],"recommendations":r[7],"date":r[8]} for r in rows]

def get_resume_by_id(resume_id, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
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
    return {"id":r[0],"name":r[1],"score":r[2],"matched":r[3],"missing":r[4],
            "rank":r[5],"job_description":r[6],"recommendations":r[7],"date":r[8]}


# ── Interview sessions ────────────────────────────────────────────────────────
def save_interview(user_id, resume_id, questions, answers, results,
                   overall_score, level, job_suggestions):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        """INSERT INTO interview_sessions
           (user_id,resume_id,questions,answers,results,overall_score,level,job_suggestions)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            user_id, resume_id,
            json.dumps(questions),
            json.dumps(answers),
            json.dumps(results),
            overall_score, level,
            json.dumps(job_suggestions),
        )
    )
    conn.commit()
    iid = cur.lastrowid
    conn.close()
    return iid

def get_interview_by_id(interview_id, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    if user_id:
        cur.execute(
            "SELECT id,resume_id,questions,answers,results,overall_score,level,job_suggestions,created_at FROM interview_sessions WHERE id=? AND user_id=?",
            (interview_id, user_id)
        )
    else:
        cur.execute(
            "SELECT id,resume_id,questions,answers,results,overall_score,level,job_suggestions,created_at FROM interview_sessions WHERE id=?",
            (interview_id,)
        )
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r[0], "resume_id": r[1],
        "questions":       json.loads(r[2] or "[]"),
        "answers":         json.loads(r[3] or "{}"),
        "results":         json.loads(r[4] or "[]"),
        "overall_score":   r[5], "level": r[6],
        "job_suggestions": json.loads(r[7] or "[]"),
        "date":            r[8],
    }

def get_interviews_for_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "SELECT id,resume_id,overall_score,level,job_suggestions,created_at FROM interview_sessions WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "resume_id": r[1], "overall_score": r[2],
            "level": r[3], "job_suggestions": json.loads(r[4] or "[]"), "date": r[5]
        }
        for r in rows
    ]