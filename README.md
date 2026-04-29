# 🤖 AI Powered Recruitment System

> An intelligent resume analyzer that gives instant ATS scores, role-specific rankings, skill gap analysis, and downloadable PDF reports — built with Python + Flask + Vanilla JS.

**Live Demo →** [ai-powered-recruitment-seven.vercel.app](https://ai-powered-recruitment-seven.vercel.app)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Resume Upload** | Drag & drop PDF, DOC, DOCX |
| 🎯 **Job Description Matching** | Paste a JD for role-specific ATS scoring |
| 🤖 **AI Scoring** | Keyword + TF-IDF cosine similarity scoring |
| 🏆 **Ranking** | Elite / Gold / Silver / Bronze tiers |
| 💡 **Recommendations** | Skill gap suggestions based on missing keywords |
| 📥 **PDF Report** | Download a formatted analysis report |
| 👤 **User Auth** | Register / Login to save and track your history |
| 📊 **Dashboard** | View all past analyses with score charts |

---

## 🗂 Project Structure

```
AI-Powered-Recruitment/
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py        # SQLite (users, sessions, resumes)
│   │   ├── resume_parser.py   # PDF/DOCX text extraction
│   │   ├── scoring_engine.py  # Keyword + TF-IDF scoring
│   │   ├── ranking_engine.py  # Score → rank label
│   │   ├── recommendation.py  # Skill gap suggestions
│   │   ├── vector_store.py    # Pinecone vector similarity (optional)
│   │   ├── ml_model.py        # TF-IDF ML model
│   │   ├── skill_engine.py    # Skill extraction
│   │   └── pdf_report.py      # ReportLab PDF generation
│   ├── uploads/               # Uploaded resume files (gitignored)
│   ├── app.py                 # Flask API
│   ├── requirements.txt
│   └── Procfile               # For Render deployment
└── frontend/
    ├── index.html             # Main upload page
    ├── history.html           # Dashboard
    ├── login.html             # Login page
    ├── register.html          # Register page
    ├── app.js                 # Main JS logic
    ├── auth.js                # Auth helpers
    └── style.css              # Styles
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/SagnikAB/AI-Powered-Recruitment-.git
cd AI-Powered-Recruitment-

# 2. Set up backend
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

# 3. Run backend
python app.py
# → Running on http://localhost:5000

# 4. Open frontend
# Just open frontend/index.html in your browser
```

### Environment Variables

Set these in Railway (or a `.env` file locally):

| Variable | Required | Description |
|---|---|---|
| `PINECONE_API_KEY` | Optional | Enables vector similarity scoring |
| `PORT` | Auto-set | Railway sets this automatically |

> The app works fully without Pinecone — vector scoring is gracefully skipped.

---

## 🌐 Deployment

### Backend → Railway
1. Push to GitHub
2. Connect repo to [Railway](https://railway.app)
3. Set root directory to `backend/`
4. Add `PINECONE_API_KEY` in Variables (optional)
5. Railway auto-deploys on every push ✅

### Frontend → Vercel
1. Connect repo to [Vercel](https://vercel.com)
2. Set root directory to `frontend/`
3. Vercel auto-deploys on every push ✅

---

## 🔌 API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET`  | `/` | — | Health check |
| `POST` | `/api/auth/register` | — | Register new user |
| `POST` | `/api/auth/login` | — | Login, returns token |
| `POST` | `/api/auth/logout` | Bearer | Logout |
| `GET`  | `/api/auth/me` | Bearer | Get current user |
| `POST` | `/api/analyze` | Optional | Analyze resume |
| `GET`  | `/api/history` | Optional | Get past analyses |
| `GET`  | `/api/report/:id` | Optional | Download PDF report |

---

## 🛠 Tech Stack

**Backend**
- Python 3 · Flask · SQLite
- scikit-learn (TF-IDF scoring)
- pdfplumber + PyPDF2 (PDF parsing)
- python-docx (DOCX parsing)
- ReportLab (PDF generation)
- Pinecone (optional vector similarity)

**Frontend**
- Vanilla HTML · CSS · JavaScript
- Chart.js (dashboard charts)
- Deployed on Vercel

---

## 📸 Screenshots

| Upload & Analyze | Dashboard |
|---|---|
| Drag & drop resume, paste JD, get instant results | View history, download PDF reports |

---

## 🤝 Contributing

Pull requests are welcome! For major changes, open an issue first.

---

## 👨‍💻 Author

**Sagnik Dam** · [GitHub @SagnikAB](https://github.com/SagnikAB)

---

## 📄 License

MIT License — free to use and modify.