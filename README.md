# Smart Resume Analyzer

AI Capstone project — an AI-powered web app that helps students analyze and
improve resumes based on industry hiring standards (ATS compatibility,
structure, technical skills, and missing keywords), using rule-based logic
(no ML/LLM calls).

## Status

- ✅ **Module 1 — Resume Upload and Parsing.** Upload a PDF/DOCX resume,
  extract its text, and store it in MySQL.
- ✅ **Module 2 — Resume Score Analyzer.** Rule-based score out of 100
  across contact info, structure, skills, projects, education, and
  completeness.
- ✅ **Module 3 — ATS Keyword Checker.** Compare a resume against
  role-specific keyword lists (Data Analyst, Web Developer, AI Engineer,
  Cloud Engineer) and get a match percentage plus improvement suggestions.
- ⬜ Module 4 — Smart Feedback System
- ⬜ Module 5 — Dashboard and Report Generation

## Tech stack

- **Backend:** Python, Flask
- **Database:** MySQL
- **Parsing:** pdfplumber (PDF), python-docx (DOCX)

## Project structure

```
smart_resume_analyzer/
├── app.py            # Flask routes
├── config.py         # DB connection settings (env-var overridable)
├── database.py       # MySQL access layer
├── extractor.py       # PDF/DOCX text extraction
├── scorer.py          # Module 2: rule-based resume scoring
├── ats_checker.py     # Module 3: rule-based ATS keyword checker
├── utils.py            # Shared helpers (boundary-safe keyword matching)
├── requirements.txt
├── static/css/style.css
└── templates/
    ├── base.html
    ├── index.html     # upload form + resume list (with score badges)
    └── view.html      # extracted text + score breakdown + ATS panel
```

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up MySQL and create a database/user matching `config.py` defaults
   (or override with environment variables):
   ```sql
   CREATE DATABASE resume_analyzer;
   CREATE USER 'resume_app'@'localhost' IDENTIFIED BY 'resume_pass123';
   GRANT ALL PRIVILEGES ON resume_analyzer.* TO 'resume_app'@'localhost';
   ```

   Environment variable overrides: `DB_HOST`, `DB_USER`, `DB_PASSWORD`,
   `DB_NAME`, `DB_PORT`.

3. Run the app:
   ```
   python app.py
   ```
   This creates the `resumes` table automatically on first run.

4. Open **http://127.0.0.1:5000** in your browser.
   (Use `127.0.0.1`, not `localhost` — some Windows setups fail to resolve
   `localhost` to the IPv4 loopback address.)

## Usage

Drag a PDF or DOCX resume onto the upload area (or click "Choose file"),
then click "Upload & process". You'll be redirected to a page showing the
extracted text, and the resume will appear in the list on the home page.
