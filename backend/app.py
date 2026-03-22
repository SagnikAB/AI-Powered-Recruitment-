from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename

# CORE IMPORTS
from core.resume_parser import extract_text
from core.scoring_engine import score_resume
from core.ranking_engine import get_rank
from core.recommendation import recommend_skills
from core.database import init_db, save_resume, get_all_resumes

# ===============================
# APP CONFIG
# ===============================
app = Flask(__name__, template_folder="../templates", static_folder="../static")
CORS(app)

app.secret_key = "super-secret-key"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB
init_db()


# ===============================
# HELPER FUNCTIONS
# ===============================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ===============================
# ROUTES (FOR TESTING / LOCAL UI)
# ===============================
@app.route("/")
def home():
    return "<h1>AI Resume Analyzer Backend Running 🚀</h1>"


@app.route("/history")
def history_page():
    data = get_all_resumes()
    return render_template("history.html", data=data)


# ===============================
# API ROUTE (MAIN FEATURE)
# ===============================
@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("resume")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        # Save file
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(filepath)

        # Extract text
        text = extract_text(filepath)

        if not text.strip():
            return jsonify({"error": "Could not extract text"}), 400

        # ML + keyword scoring
        score, matched, missing = score_resume(text)

        # Rank
        rank = get_rank(score)

        # Recommendations
        recommendations = recommend_skills(missing)

        # Save to DB
        save_resume(filename, score, matched, rank)

        # Response
        return jsonify({
            "filename": filename,
            "score": score,
            "rank": rank,
            "keywords": matched,
            "missing": missing,
            "recommendations": recommendations
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Server error"}), 500


# ===============================
# HISTORY API (FOR DASHBOARD)
# ===============================
@app.route("/api/history", methods=["GET"])
def history_api():
    try:
        data = get_all_resumes()

        formatted = []
        for row in data:
            formatted.append({
                "filename": row[1],
                "score": row[2],
                "rank": row[3],
                "keywords": row[4]
            })

        return jsonify(formatted)

    except Exception as e:
        print("DB ERROR:", e)
        return jsonify({"error": "Failed to fetch history"}), 500


# ===============================
# ERROR HANDLERS
# ===============================
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": "File too large (max 5MB)"}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404


# ===============================
# RUN SERVER (DEPLOY SAFE)
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)