import sys
import os
import uuid
import traceback

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from io import BytesIO

from core.resume_parser   import extract_text
from core.scoring_engine  import score_resume
from core.ranking_engine  import get_rank
from core.recommendation  import recommend_skills
from core.vector_store    import store_resume, match_resume
from core.pdf_report      import generate_pdf_report
from core.interview_engine import generate_questions, evaluate_all_answers, suggest_job_titles
from core.database import (
    init_db,
    register_user, login_user, logout_user, get_user_from_token,
    save_resume, get_all_resumes, get_resume_by_id,
    save_interview, get_interview_by_id, get_interviews_for_user,
)

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER    = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

# ── Helpers ───────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_token(req):
    auth = req.headers.get("Authorization", "")
    return auth.replace("Bearer ", "").strip() or req.args.get("token", "")


# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "AI Recruitment API v3 🚀"})


# ═══════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    username = (data.get("username") or "").strip()
    email    = (data.get("email")    or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not email or not password:
        return jsonify({"error": "username, email and password required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    result = register_user(username, email, password)
    if not result["success"]:
        return jsonify({"error": result["error"]}), 409
    return jsonify({"message": "Registered successfully"}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    email    = (data.get("email")    or "").strip()
    password = (data.get("password") or "").strip()
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    result = login_user(email, password)
    if not result["success"]:
        return jsonify({"error": result["error"]}), 401
    return jsonify({"token": result["token"], "username": result["username"], "user_id": result["user_id"]})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    token = get_token(request)
    if token:
        logout_user(token)
    return jsonify({"message": "Logged out"})

@app.route("/api/auth/me", methods=["GET"])
def me():
    user = get_user_from_token(get_token(request))
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(user)


# ═══════════════════════════════════════════════════════════════════
# ANALYZE
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        user    = get_user_from_token(get_token(request))
        user_id = user["id"] if user else None

        file            = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not file or file.filename == "":
            return jsonify({"error": "No file uploaded"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF, DOC, DOCX files are supported"}), 400

        filename    = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath    = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(filepath)

        text = extract_text(filepath)
        if not text.strip():
            return jsonify({"error": "Could not extract text. Is it a scanned PDF?"}), 422

        score, matched, missing = score_resume(text, job_description)

        try:
            vector_score = match_resume(text) * 100
        except Exception:
            vector_score = 0

        final_score = max(0, min(100, int(score * 0.6 + vector_score * 0.4)))

        try:
            store_resume(unique_name, text)
        except Exception:
            pass

        rank            = get_rank(final_score)
        recommendations = recommend_skills(missing)

        # Job title suggestions based on resume alone (no interview yet)
        job_suggestions = suggest_job_titles(matched, final_score)

        resume_id = save_resume(
            user_id, filename, final_score,
            matched, missing, rank,
            job_description, recommendations
        )

        return jsonify({
            "resume_id":       resume_id,
            "score":           final_score,
            "rank":            rank,
            "vector_score":    round(vector_score, 2),
            "keywords":        matched,
            "missing":         missing,
            "recommendations": recommendations,
            "job_description": job_description,
            "job_suggestions": job_suggestions,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════
# INTERVIEW — Step 1: get questions
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/interview/questions", methods=["POST"])
def get_interview_questions():
    """
    Body: { "resume_id": 5, "matched_skills": ["python","sql",...] }
    Returns a list of interview questions.
    """
    try:
        data          = request.get_json()
        matched_skills = data.get("matched_skills", [])
        resume_id     = data.get("resume_id")

        if not matched_skills:
            return jsonify({"error": "matched_skills list is required"}), 400

        questions = generate_questions(matched_skills, n=7)

        # Strip ideal answer before sending to frontend (reveal after submit)
        questions_clean = [
            {"id": q["id"], "q": q["q"], "skill": q.get("skill", "general")}
            for q in questions
        ]

        # Store full questions in session cache using resume_id as key
        # We return them with ideal answers stripped; full data used on submit
        return jsonify({
            "questions":  questions_clean,
            "full":       questions,   # frontend stores this temporarily
            "resume_id":  resume_id,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════
# INTERVIEW — Step 2: submit answers
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/interview/submit", methods=["POST"])
def submit_interview():
    """
    Body: {
        "resume_id": 5,
        "ats_score": 72,
        "matched_skills": [...],
        "questions": [...full question objects...],
        "answers": {"0": "...", "1": "...", ...}
    }
    """
    try:
        user    = get_user_from_token(get_token(request))
        user_id = user["id"] if user else None

        data           = request.get_json()
        resume_id      = data.get("resume_id")
        ats_score      = data.get("ats_score", 0)
        matched_skills = data.get("matched_skills", [])
        questions      = data.get("questions", [])
        answers        = data.get("answers", {})

        if not questions or not answers:
            return jsonify({"error": "questions and answers are required"}), 400

        # Evaluate all answers
        evaluation = evaluate_all_answers(questions, answers)

        # Suggest job titles using both ATS score + interview score
        job_suggestions = suggest_job_titles(
            matched_skills,
            ats_score,
            evaluation["overall_score"]
        )

        # Save to DB
        interview_id = save_interview(
            user_id, resume_id,
            questions, answers,
            evaluation["results"],
            evaluation["overall_score"],
            evaluation["level"],
            job_suggestions,
        )

        return jsonify({
            "interview_id":  interview_id,
            "overall_score": evaluation["overall_score"],
            "level":         evaluation["level"],
            "results":       evaluation["results"],
            "job_suggestions": job_suggestions,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════
# INTERVIEW — history & single fetch
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/interview/history", methods=["GET"])
def interview_history():
    try:
        user = get_user_from_token(get_token(request))
        if not user:
            return jsonify([])
        return jsonify(get_interviews_for_user(user["id"]))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/interview/<int:interview_id>", methods=["GET"])
def get_interview(interview_id):
    try:
        user    = get_user_from_token(get_token(request))
        user_id = user["id"] if user else None
        data    = get_interview_by_id(interview_id, user_id)
        if not data:
            return jsonify({"error": "Not found"}), 404
        return jsonify(data)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════
# HISTORY & PDF
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/history", methods=["GET"])
def history():
    try:
        user    = get_user_from_token(get_token(request))
        user_id = user["id"] if user else None
        return jsonify(get_all_resumes(user_id))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/report/<int:resume_id>", methods=["GET"])
def download_report(resume_id):
    try:
        user    = get_user_from_token(get_token(request))
        user_id = user["id"] if user else None
        data    = get_resume_by_id(resume_id, user_id)
        if not data:
            return jsonify({"error": "Report not found"}), 404
        pdf_bytes = generate_pdf_report(data)
        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"resume_report_{resume_id}.pdf"
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)