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


def init_db():
    """Create the resumes table if it doesn't already exist."""
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
    """Return a list of (id, filename, file_type, uploaded_at) for all resumes,
    newest first."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, filename, file_type, uploaded_at
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
