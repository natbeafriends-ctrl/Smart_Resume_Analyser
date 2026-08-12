"""
database.py
-----------
Handles all MySQL database operations for the Smart Resume Analyzer.

Module 1 responsibility: Store resume information (filename, file type,
extracted text, upload timestamp) so later modules (scoring, ATS checking,
feedback, dashboard) can read it back.

Uses mysql-connector-python. Connection settings live in config.py.
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime

from config import DB_CONFIG


def get_connection():
    """Open and return a new MySQL connection using settings from config.py."""
    return mysql.connector.connect(**DB_CONFIG)


def _column_exists(cursor, table, column):
    """Check information_schema so we never try to add a column twice."""
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
    """, (DB_CONFIG["database"], table, column))
    (count,) = cursor.fetchone()
    return count > 0


def _ensure_score_columns(conn, cursor):
    """Add Module 2's score columns to the resumes table if they're not
    already there. This lets a database created back in Module 1 (before
    scoring existed) pick up the new columns without losing any existing
    rows — no DROP TABLE, no data loss."""
    if not _column_exists(cursor, "resumes", "total_score"):
        cursor.execute("ALTER TABLE resumes ADD COLUMN total_score INT DEFAULT NULL")
    if not _column_exists(cursor, "resumes", "score_breakdown"):
        cursor.execute("ALTER TABLE resumes ADD COLUMN score_breakdown LONGTEXT DEFAULT NULL")
    conn.commit()


def init_db():
    """Create the resumes table if it doesn't already exist, and ensure
    Module 2's score columns are present either way."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(10) NOT NULL,
                    extracted_text LONGTEXT NOT NULL,
                    uploaded_at DATETIME NOT NULL
                )
            """)
            conn.commit()
            _ensure_score_columns(conn, cursor)
        finally:
            cursor.close()
    finally:
        conn.close()


def save_resume(filename, file_type, extracted_text):
    """Insert a new resume record. Returns the new record's id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO resumes (filename, file_type, extracted_text, uploaded_at)
                VALUES (%s, %s, %s, %s)
            """, (filename, file_type, extracted_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
    finally:
        conn.close()


def get_all_resumes():
    """Return a list of (id, filename, file_type, uploaded_at, total_score)
    for all resumes, newest first. total_score is None if not yet scored."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, filename, file_type, uploaded_at, total_score
                FROM resumes
                ORDER BY id DESC
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conn.close()


def get_resume_by_id(resume_id):
    """Return the full record (id, filename, file_type, extracted_text, uploaded_at)
    for a single resume, or None if not found."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, filename, file_type, extracted_text, uploaded_at
                FROM resumes WHERE id = %s
            """, (resume_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
    finally:
        conn.close()


def save_score(resume_id, total_score, score_breakdown_json):
    """Save (or overwrite) the score and category breakdown for a resume.
    score_breakdown_json should already be a JSON string (see scorer.py's
    score_resume() output, json.dumps'd by the caller)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE resumes SET total_score = %s, score_breakdown = %s
                WHERE id = %s
            """, (total_score, score_breakdown_json, resume_id))
            conn.commit()
        finally:
            cursor.close()
    finally:
        conn.close()


def get_score_by_id(resume_id):
    """Return (total_score, score_breakdown_json) for a resume.
    Both are None if the resume hasn't been scored yet (or doesn't exist)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT total_score, score_breakdown FROM resumes WHERE id = %s
            """, (resume_id,))
            row = cursor.fetchone()
            return row if row else (None, None)
        finally:
            cursor.close()
    finally:
        conn.close()
