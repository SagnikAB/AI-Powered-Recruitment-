import sys
import os
import uuid

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# CORE IMPORTS
from core.resume_parser import extract_text
from core.scoring_engine import score_resume
from core.ranking_engine import get_rank
from core.recommendation import recommend_skills
from core.database import init_db, save_resume, get_all_resumes
from core.vector_store import store_resume, match_resume

# ================= APP CONFIG =================
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

# ================= HELPER =================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ================= HEALTH =================
@app.route("/")
def home():
    return "Backend running 🚀"

# ================= ANALYZE =================
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

        # ================= KEYWORD SCORE =================
        score, matched, missing = score_resume(text)

        # ================= VECTOR SCORE =================
        try:
            vector_score = match_resume(text) * 100
        except Exception as e:
            print("Vector error:", e)
            vector_score = 0

        # ================= FINAL SCORE =================
        final_score = int((score * 0.6) + (vector_score * 0.4))

        # ================= STORE VECTOR =================
        try:
            store_resume(unique_name, text)
        except Exception as e:
            print("Store error:", e)

        # ================= RANK =================
        rank = get_rank(final_score)

        # ================= RECOMMEND =================
        recommendations = recommend_skills(missing)

        # ================= SAVE =================
        save_resume(filename, final_score, matched, rank)

        return jsonify({
            "score": final_score,
            "rank": rank,
            "vector_score": vector_score,
            "keywords": matched,
            "recommendations": recommendations
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Server error"}), 500


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)