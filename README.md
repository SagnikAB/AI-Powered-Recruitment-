# 🤖 AI-Powered Smart Interview & Resume Evaluation System

An intelligent web application that automates resume screening and interview evaluation using Machine Learning and Natural Language Processing (NLP).

---

## 🚀 Features

* 📄 Upload resumes (PDF/DOC/DOCX)
* 🧠 AI-based resume analysis
* 🎯 Job description matching
* 📊 Resume scoring system
* 🏆 Candidate ranking (Elite, Gold, Silver, Bronze)
* 💡 Smart recommendations for improvement
* 🎤 AI-generated interview questions
* 📝 Answer evaluation system
* 📥 PDF report generation

---

## 🧠 How It Works

1. User uploads a resume
2. Text is extracted from the document
3. Skills and keywords are identified
4. Resume is scored based on relevance
5. AI generates interview questions
6. Answers are evaluated
7. Final score and recommendations are provided

---

## 🛠️ Tech Stack

**Frontend:**

* HTML, CSS, JavaScript

**Backend:**

* Python (Flask)

**Libraries & Tools:**

* scikit-learn (ML scoring)
* spaCy (NLP)
* PyPDF2 / pdfplumber (resume parsing)
* python-docx
* reportlab (PDF generation)

---

## 📁 Project Structure

```
AI-Powered-Recruitment/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── core/
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── auth.js
│
└── README.md
```

---

## ⚙️ Installation (Local Setup)

### 1. Clone the repository

```
git clone https://github.com/your-username/AI-Powered-Recruitment.git
cd AI-Powered-Recruitment
```

### 2. Install dependencies

```
cd backend
pip install -r requirements.txt
```

### 3. Run the backend

```
python app.py
```

### 4. Open frontend

Open `frontend/index.html` in your browser

---

## 🌐 Deployment (Render)

This project is deployed using **Render**.

### Steps:

1. Push your code to GitHub
2. Go to Render → New Web Service
3. Connect your GitHub repository
4. Configure:

```
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

5. Deploy and access your live API

---

## 📌 API Example

### Analyze Resume

```
POST /api/analyze
```

Form Data:

* resume (file)
* job_description (optional)

---

## 🎯 Use Cases

* Automating recruitment process
* Resume screening
* Interview preparation
* Skill gap analysis

---

## 🚀 Future Scope

* Video interview analysis
* Voice-based evaluation
* Advanced AI models (LLMs)
* Recruiter dashboard

---

## 👨‍💻 Author

Sagnik Dam

---

## ⭐ Acknowledgement

This project was developed as part of academic work to explore AI-driven recruitment systems.

---
