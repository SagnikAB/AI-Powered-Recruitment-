import sys
import os

# Fix import path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import uuid
from werkzeug.utils import secure_filename

# ================= CORE MODULES =================
from core.resume_parser import extract_text
from core.scoring_engine import score_resume
from core.ranking_engine import get_rank
from core.recommendation import recommend_skills
from core.database import init_db, save_resume, get_all_resumes

# 🔥 VECTOR (PINECONE)
from core.vector_store import store_resume, match_resume
# ================= APP CONFIG =================
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Init DB
init_db()

# ================= HELPERS =================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ================= ROUTES =================

@app.route("/")
def home():
    return "<h2>🚀 AI Resume Analyzer Backend Running</h2>"


# ================= MAIN API =================
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

        # ================= SAVE FILE =================
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(filepath)

        # ================= EXTRACT TEXT =================
        text = extract_text(filepath)

        if not text or not text.strip():
            return jsonify({"error": "Could not extract text"}), 400

        # ================= VECTOR SCORE =================
        try:
            vector_score = match_resume(text) * 100
        except Exception as e:
            print("Vector Error:", e)
            vector_score = 0

        # ================= KEYWORD SCORE =================
        score, matched, missing = score_resume(text)

        # ================= HYBRID SCORE =================
        final_score = int((score * 0.6) + (vector_score * 0.4))

        # ================= STORE VECTOR =================
        try:
            store_resume(unique_name, text)
        except Exception as e:
            print("Store Vector Error:", e)

        # ================= RANK =================
        rank = get_rank(final_score)

        # ================= RECOMMENDATIONS =================
        recommendations = recommend_skills(missing)

        # ================= SAVE TO DB =================
        save_resume(filename, final_score, matched, rank)

        # ================= RESPONSE =================
        return jsonify({
            "filename": filename,
            "score": final_score,
            "rank": rank,
            "vector_score": round(vector_score, 2),
            "keywords": matched,
            "missing": missing,
            "recommendations": recommendations
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"error": "Server error"}), 500


# ================= HISTORY API =================
@app.route("/api/history", methods=["GET"])
def history():
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
        print("History Error:", e)
        return jsonify({"error": "Failed to fetch history"}), 500


# ================= ERROR HANDLERS =================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404


@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": "File too large"}), 413


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)