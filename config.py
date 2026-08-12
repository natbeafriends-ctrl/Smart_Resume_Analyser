"""
config.py
---------
MySQL connection settings for the Smart Resume Analyzer.

Edit these values to match your own MySQL server, or set them via
environment variables (recommended for anything beyond local testing,
so credentials aren't hard-coded in source control).
"""

import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "resume_app"),
    "password": os.environ.get("DB_PASSWORD", "resume_pass123"),
    "database": os.environ.get("DB_NAME", "resume_analyzer"),
    "port": int(os.environ.get("DB_PORT", 3306)),
}
