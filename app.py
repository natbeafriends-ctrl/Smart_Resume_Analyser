"""
app.py
------
Smart Resume Analyzer - Module 1 (upload/parsing) + Module 2 (scoring)
+ Module 3 (ATS keyword checker) + Module 4 (smart feedback)
+ Module 5 (dashboard)

Routes:
  GET  /                       -> Upload form + list of previously uploaded resumes
  POST /upload                  -> Handle file upload, extract text, score, feedback, store in DB
  GET  /resume/<id>             -> View extracted text, score, ATS result, and suggestions
  GET  /resume/<id>/dashboard   -> Visual summary dashboard (score, ATS %, missing skills, suggestions)
  POST /resume/<id>/rescore     -> Recompute and re-save a resume's score
  POST /resume/<id>/ats_check   -> Run the ATS keyword checker for a chosen role
  POST /resume/<id>/feedback    -> Manually regenerate smart feedback suggestions
"""

import os
import json
import uuid
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename

from database import (
    init_db, save_resume, get_all_resumes, get_resume_by_id,
    save_score, get_score_by_id, save_ats_result, get_ats_result_by_id,
    save_feedback, get_feedback_by_id,
)
from extractor import extract_text
from scorer import score_resume
from ats_checker import check_ats, ROLE_KEYWORDS
from feedback import generate_feedback

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx"}

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # fine for local dev/demo purposes
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload size

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _regenerate_feedback(resume_id, extracted_text):
    """Module 4: rebuild the smart feedback list using whatever Module 2
    score and Module 3 ATS data currently exist for this resume, and save
    it. Called after upload, rescore, and ats_check so feedback always
    reflects the latest data from the other two modules."""
    _, score_breakdown_json = get_score_by_id(resume_id)
    score_result = None
    if score_breakdown_json:
        score_result = {
            "categories": json.loads(score_breakdown_json),
        }

    _, ats_result_json = get_ats_result_by_id(resume_id)
    ats_result = json.loads(ats_result_json) if ats_result_json else None

    feedback = generate_feedback(extracted_text, score_result=score_result, ats_result=ats_result)
    save_feedback(resume_id, json.dumps(feedback))


def _load_resume_context(resume_id):
    """Fetch a resume plus everything Modules 2-4 have computed for it.
    Shared by view_resume and the Module 5 dashboard so both pages stay in
    sync without duplicating the fetch/parse logic. Returns None if the
    resume doesn't exist."""
    resume = get_resume_by_id(resume_id)
    if resume is None:
        return None

    total_score, score_breakdown_json = get_score_by_id(resume_id)
    categories = json.loads(score_breakdown_json) if score_breakdown_json else None

    ats_role, ats_result_json = get_ats_result_by_id(resume_id)
    ats_result = json.loads(ats_result_json) if ats_result_json else None

    feedback_json = get_feedback_by_id(resume_id)
    feedback = json.loads(feedback_json) if feedback_json else None

    return {
        "resume": resume,
        "total_score": total_score,
        "categories": categories,
        "ats_result": ats_result,
        "feedback": feedback,
        "roles": list(ROLE_KEYWORDS.keys()),
    }


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
    _regenerate_feedback(resume_id, extracted_text)

    flash(f"'{original_filename}' uploaded and processed successfully!")
    return redirect(url_for("view_resume", resume_id=resume_id))


@app.route("/resume/<int:resume_id>")
def view_resume(resume_id):
    context = _load_resume_context(resume_id)
    if context is None:
        flash("Resume not found.")
        return redirect(url_for("index"))
    return render_template("view.html", **context)


@app.route("/resume/<int:resume_id>/dashboard")
def dashboard(resume_id):
    """Module 5: visual summary of a resume's score, ATS compatibility,
    missing skills, and suggestions in one interactive, printable view."""
    context = _load_resume_context(resume_id)
    if context is None:
        flash("Resume not found.")
        return redirect(url_for("index"))
    return render_template("dashboard.html", **context)


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
    _regenerate_feedback(resume_id, extracted_text)
    flash("Score recalculated.")
    return redirect(url_for("view_resume", resume_id=resume_id))


@app.route("/resume/<int:resume_id>/ats_check", methods=["POST"])
def ats_check(resume_id):
    """Run the ATS keyword checker (Module 3) against the resume for a
    user-selected target role, and save the result."""
    resume = get_resume_by_id(resume_id)
    if resume is None:
        flash("Resume not found.")
        return redirect(url_for("index"))

    role = request.form.get("role")
    if role not in ROLE_KEYWORDS:
        flash("Please select a valid job role.")
        return redirect(url_for("view_resume", resume_id=resume_id))

    _, _, _, extracted_text, _ = resume
    result = check_ats(extracted_text, role)
    save_ats_result(resume_id, role, json.dumps(result))
    _regenerate_feedback(resume_id, extracted_text)
    flash(f"ATS check complete for {role}.")
    return redirect(url_for("view_resume", resume_id=resume_id))


@app.route("/resume/<int:resume_id>/feedback", methods=["POST"])
def refresh_feedback(resume_id):
    """Manually regenerate Module 4's smart feedback suggestions, e.g. after
    running/re-running Module 2 or 3 checks separately."""
    resume = get_resume_by_id(resume_id)
    if resume is None:
        flash("Resume not found.")
        return redirect(url_for("index"))

    _, _, _, extracted_text, _ = resume
    _regenerate_feedback(resume_id, extracted_text)
    flash("Suggestions refreshed.")
    return redirect(url_for("view_resume", resume_id=resume_id))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
