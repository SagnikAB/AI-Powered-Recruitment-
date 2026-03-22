import sys
import os
import uuid
import traceback

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from io import BytesIO

from core.resume_parser import extract_text
from core.scoring_engine import score_resume
from core.ranking_engine import get_rank
from core.recommendation import recommend_skills
from core.vector_store import store_resume, match_resume
from core.pdf_report import generate_pdf_report
from core.database import (
    init_db,
    register_user, login_user, logout_user, get_user_from_token,
    save_resume, get_all_resumes, get_resume_by_id
)

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
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
    return jsonify({"status": "ok", "message": "AI Recruitment API v2 🚀"})


# ═════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    username = (data.get("username") or "").strip()
    email    = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), 400
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
    email    = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    result = login_user(email, password)
    if not result["success"]:
        return jsonify({"error": result["error"]}), 401
    return jsonify({
        "token":    result["token"],
        "username": result["username"],
        "user_id":  result["user_id"]
    })


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    token = get_token(request)
    if token:
        logout_user(token)
    return jsonify({"message": "Logged out"})


@app.route("/api/auth/me", methods=["GET"])
def me():
    token = get_token(request)
    user = get_user_from_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(user)


# ═════════════════════════════════════════════════════════════════════════════
# ANALYZE ROUTE
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        # Auth (optional — guests get user_id=None)
        token = get_token(request)
        user  = get_user_from_token(token)
        user_id = user["id"] if user else None

        file = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        if not file:
            return jsonify({"error": "No file uploaded"}), 400
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF, DOC, DOCX files are supported"}), 400

        # Save file
        filename    = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath    = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(filepath)

        # Extract text
        text = extract_text(filepath)
        if not text.strip():
            return jsonify({"error": "Could not extract text. Is it a scanned PDF?"}), 422

        # Score (with optional job description)
        score, matched, missing = score_resume(text, job_description)

        # Vector score
        try:
            vector_score = match_resume(text) * 100
        except Exception as e:
            print(f"Vector error: {e}")
            vector_score = 0

        # Final score
        final_score = int((score * 0.6) + (vector_score * 0.4))
        final_score = max(0, min(100, final_score))

        # Store vector
        try:
            store_resume(unique_name, text)
        except Exception as e:
            print(f"Store error: {e}")

        rank            = get_rank(final_score)
        recommendations = recommend_skills(missing)

        # Save to DB
        resume_id = save_resume(
            user_id, filename, final_score,
            matched, missing, rank,
            job_description, recommendations
        )

        return jsonify({
            "resume_id":     resume_id,
            "score":         final_score,
            "rank":          rank,
            "vector_score":  round(vector_score, 2),
            "keywords":      matched,
            "missing":       missing,
            "recommendations": recommendations,
            "job_description": job_description,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# HISTORY ROUTE
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/history", methods=["GET"])
def history():
    try:
        token   = get_token(request)
        user    = get_user_from_token(token)
        user_id = user["id"] if user else None
        resumes = get_all_resumes(user_id)
        return jsonify(resumes)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# PDF DOWNLOAD ROUTE
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/api/report/<int:resume_id>", methods=["GET"])
def download_report(resume_id):
    try:
        token   = get_token(request)
        user    = get_user_from_token(token)
        user_id = user["id"] if user else None

        data = get_resume_by_id(resume_id, user_id)
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


# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)