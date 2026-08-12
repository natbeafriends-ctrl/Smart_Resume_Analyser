"""
app.py
------
Smart Resume Analyzer - Module 1: Resume Upload and Parsing

Routes:
  GET  /            -> Show upload form + list of previously uploaded resumes
  POST /upload       -> Handle file upload, extract text, store in DB
  GET  /resume/<id>  -> View extracted text for a specific resume
"""

import os
import uuid
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename

from database import init_db, save_resume, get_all_resumes, get_resume_by_id
from extractor import extract_text

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx"}

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # fine for local dev/demo purposes
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload size

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    resumes = get_all_resumes()
    return render_template("index.html", resumes=resumes)


@app.route("/upload", methods=["POST"])
def upload():
    if "resume" not in request.files:
        flash("No file part in the request.")
        return redirect(url_for("index"))

    file = request.files["resume"]

    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Only PDF or DOCX files are allowed.")
        return redirect(url_for("index"))

    # Original name is what we display and store in the DB; it's never used
    # directly as a filesystem path.
    original_filename = secure_filename(file.filename)
    if not original_filename:
        flash("Invalid filename.")
        return redirect(url_for("index"))

    file_extension = original_filename.rsplit(".", 1)[1].lower()

    # Prefix with a UUID for the on-disk name so two uploads with the same
    # filename never collide or overwrite each other.
    stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], stored_filename)
    file.save(filepath)

    try:
        extracted_text = extract_text(filepath, file_extension)
    except Exception as e:
        flash(f"Could not extract text: {e}")
        os.remove(filepath)  # don't leave an orphaned file we can't process
        return redirect(url_for("index"))

    if not extracted_text:
        flash("Warning: no text could be extracted from this file (it may be a scanned/image-based document).")

    resume_id = save_resume(original_filename, file_extension, extracted_text)
    flash(f"'{original_filename}' uploaded and processed successfully!")
    return redirect(url_for("view_resume", resume_id=resume_id))


@app.route("/resume/<int:resume_id>")
def view_resume(resume_id):
    resume = get_resume_by_id(resume_id)
    if resume is None:
        flash("Resume not found.")
        return redirect(url_for("index"))
    return render_template("view.html", resume=resume)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
