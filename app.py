"""
app.py
------
Smart Resume Analyzer - Module 1 (upload/parsing) + Module 2 (scoring)

Routes:
  GET  /                     -> Upload form + list of previously uploaded resumes
  POST /upload                -> Handle file upload, extract text, score, store in DB
  GET  /resume/<id>           -> View extracted text + score breakdown for a resume
  POST /resume/<id>/rescore   -> Recompute and re-save a resume's score
"""

import os
import json
import uuid
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename

from database import (
    init_db, save_resume, get_all_resumes, get_resume_by_id,
    save_score, get_score_by_id,
)
from extractor import extract_text
from scorer import score_resume

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

    result = score_resume(extracted_text)
    save_score(resume_id, result["total_score"], json.dumps(result["categories"]))

    flash(f"'{original_filename}' uploaded and processed successfully!")
    return redirect(url_for("view_resume", resume_id=resume_id))


@app.route("/resume/<int:resume_id>")
def view_resume(resume_id):
    resume = get_resume_by_id(resume_id)
    if resume is None:
        flash("Resume not found.")
        return redirect(url_for("index"))

    total_score, score_breakdown_json = get_score_by_id(resume_id)
    categories = json.loads(score_breakdown_json) if score_breakdown_json else None

    return render_template(
        "view.html", resume=resume, total_score=total_score, categories=categories
    )


@app.route("/resume/<int:resume_id>/rescore", methods=["POST"])
def rescore(resume_id):
    """Recompute and re-save the score for a resume — convenience route for
    re-running Module 2's rule-based logic after scorer.py changes, without
    needing to re-upload the file."""
    resume = get_resume_by_id(resume_id)
    if resume is None:
        flash("Resume not found.")
        return redirect(url_for("index"))

    _, _, _, extracted_text, _ = resume
    result = score_resume(extracted_text)
    save_score(resume_id, result["total_score"], json.dumps(result["categories"]))
    flash("Score recalculated.")
    return redirect(url_for("view_resume", resume_id=resume_id))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
