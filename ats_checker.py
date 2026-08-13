"""
ats_checker.py
--------------
Rule-based ATS Keyword Checker (Module 3).

Compares a resume's extracted text against a curated keyword list for a
chosen target job role and reports which keywords are present, which are
missing, an ATS match percentage, and short improvement suggestions for
each gap. Pure keyword lookup — no ML/LLM calls — per the capstone's
rule-based AI logic requirement.
"""

from utils import keyword_in_text

# Curated per-role keyword lists. Order matters for display, so keep the
# most important/common keywords first within each role.
ROLE_KEYWORDS = {
    "Data Analyst": [
        "sql", "excel", "python", "tableau", "power bi", "statistics",
        "data visualization", "data cleaning", "pandas", "numpy", "r",
        "dashboard", "kpi", "reporting",
    ],
    "Web Developer": [
        "html", "css", "javascript", "react", "angular", "vue", "node.js",
        "rest api", "git", "responsive design", "typescript", "sql",
        "mongodb", "testing",
    ],
    "AI Engineer": [
        "python", "machine learning", "deep learning", "tensorflow",
        "pytorch", "nlp", "computer vision", "scikit-learn", "pandas",
        "numpy", "neural networks", "model deployment", "sql", "git",
    ],
    "Cloud Engineer": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "ci/cd", "linux", "networking", "cloud security", "devops",
        "python", "bash", "infrastructure as code", "monitoring",
    ],
}

# Friendly display names for keywords that read awkwardly raw (e.g. in a
# sentence like "Add ci/cd skill" vs "Add CI/CD skill").
DISPLAY_NAMES = {
    "sql": "SQL", "html": "HTML", "css": "CSS", "aws": "AWS", "gcp": "GCP",
    "ci/cd": "CI/CD", "nlp": "NLP", "kpi": "KPI reporting",
    "node.js": "Node.js", "rest api": "REST API", "r": "R",
    "javascript": "JavaScript", "typescript": "TypeScript",
    "mongodb": "MongoDB", "tensorflow": "TensorFlow", "pytorch": "PyTorch",
    "scikit-learn": "scikit-learn", "power bi": "Power BI",
}

# Keywords that read better as "Include X projects" or "Mention X
# experience" rather than the default "Add X skill" suggestion phrasing.
PROJECT_STYLE_KEYWORDS = {"react", "angular", "vue", "node.js"}
MENTION_STYLE_KEYWORDS = {
    "aws", "azure", "gcp", "cloud security", "devops", "kubernetes",
    "docker", "terraform", "infrastructure as code",
}


def _display(keyword):
    return DISPLAY_NAMES.get(keyword, keyword.title())


def _suggestion_for(keyword):
    """Short, human-readable improvement suggestion for a missing keyword,
    in the style of the spec's examples ("Add SQL skill", "Include React
    projects", "Mention cloud technologies")."""
    name = _display(keyword)
    if keyword in PROJECT_STYLE_KEYWORDS:
        return f"Include {name} projects."
    if keyword in MENTION_STYLE_KEYWORDS:
        return f"Mention {name} experience."
    return f"Add {name} skill."


def check_ats(text, role):
    """
    Compare resume text against the keyword list for `role`.

    Returns:
        {
            "role": str,
            "match_percent": int (0-100),
            "matched": [str, ...],      # display-formatted, found in resume
            "missing": [str, ...],      # display-formatted, not found
            "suggestions": [str, ...],  # one per missing keyword
        }

    Raises ValueError if `role` isn't in ROLE_KEYWORDS.
    """
    if role not in ROLE_KEYWORDS:
        raise ValueError(f"Unknown role: {role!r}. Valid roles: {list(ROLE_KEYWORDS)}")

    text_lower = (text or "").lower()
    keywords = ROLE_KEYWORDS[role]

    matched_raw = [kw for kw in keywords if keyword_in_text(kw, text_lower)]
    missing_raw = [kw for kw in keywords if kw not in matched_raw]

    match_percent = round((len(matched_raw) / len(keywords)) * 100) if keywords else 0

    return {
        "role": role,
        "match_percent": match_percent,
        "matched": [_display(kw) for kw in matched_raw],
        "missing": [_display(kw) for kw in missing_raw],
        "suggestions": [_suggestion_for(kw) for kw in missing_raw],
    }
