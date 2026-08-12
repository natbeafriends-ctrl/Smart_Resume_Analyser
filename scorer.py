"""
scorer.py
---------
Rule-based Resume Score Analyzer (Module 2).

No ML/LLM calls — every score below comes from deterministic pattern
matching and keyword lookups against the resume's extracted text, per the
capstone's "rule-based AI logic" requirement.

Six weighted categories, 100 points total:
    Contact Information     15
    Resume Structure         15
    Skills Section            20
    Projects Section          20
    Education Details         15
    Resume Completeness       15

score_resume(text) -> dict:
    {
        "total_score": int,
        "categories": {
            "contact_info":  {"score": int, "max": int, "details": [str, ...]},
            "structure":     {...},
            "skills":        {...},
            "projects":      {...},
            "education":     {...},
            "completeness":  {...},
        }
    }

The "details" lists are short, human-readable strings meant to feed the
Module 5 dashboard directly (e.g. "Email address found.", "No phone number
detected.").
"""

import re

# ---------------------------------------------------------------------------
# Reference keyword lists used by the rule-based checks below.
# ---------------------------------------------------------------------------

SECTION_HEADERS = {
    "experience": [r"\bexperience\b", r"\bwork history\b", r"\bemployment\b"],
    "education": [r"\beducation\b", r"\bacademic\b"],
    "skills": [r"\bskills\b", r"\btechnical skills\b", r"\bcore competenc"],
    "projects": [r"\bprojects?\b"],
    "summary": [r"\bsummary\b", r"\bobjective\b", r"\bprofile\b"],
}

DEGREE_KEYWORDS = [
    r"\bb\.?\s?tech\b", r"\bb\.?\s?e\.?\b", r"\bb\.?\s?sc\b", r"\bbachelor",
    r"\bm\.?\s?tech\b", r"\bm\.?\s?sc\b", r"\bmaster", r"\bphd\b", r"\bmba\b",
    r"\bdiploma\b", r"\bassociate degree\b",
]

INSTITUTION_KEYWORDS = [
    r"\buniversity\b", r"\bcollege\b", r"\binstitute\b", r"\bgpa\b", r"%",
]

COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql",
    "html", "css", "react", "angular", "vue", "node.js", "node", "flask",
    "django", "spring", "mysql", "postgresql", "mongodb", "aws", "azure",
    "gcp", "docker", "kubernetes", "git", "linux", "excel", "power bi",
    "tableau", "machine learning", "deep learning", "nlp", "pandas",
    "numpy", "tensorflow", "pytorch", "rest api", "graphql", "agile",
    "scrum", "communication", "leadership", "teamwork", "problem solving",
]

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{3,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}")
LINK_PATTERN = re.compile(r"(linkedin\.com|github\.com|portfolio|behance\.net)", re.IGNORECASE)
BULLET_PATTERN = re.compile(r"^[\-\*\u2022]\s+", re.MULTILINE)


def _find_section_headers(text_lower):
    """Return the set of section names found via SECTION_HEADERS patterns."""
    found = set()
    for name, patterns in SECTION_HEADERS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.add(name)
                break
    return found


def _score_contact_info(text, text_lower):
    max_score = 15
    score = 0
    details = []

    if EMAIL_PATTERN.search(text):
        score += 5
        details.append("Email address found.")
    else:
        details.append("No email address detected.")

    if PHONE_PATTERN.search(text):
        score += 5
        details.append("Phone number found.")
    else:
        details.append("No phone number detected.")

    if LINK_PATTERN.search(text_lower):
        score += 5
        details.append("LinkedIn, GitHub, or portfolio link found.")
    else:
        details.append("No LinkedIn, GitHub, or portfolio link detected.")

    return {"score": score, "max": max_score, "details": details}


def _score_structure(headers_found):
    max_score = 15
    per_header = 3
    score = 0
    details = []

    for name in ["summary", "experience", "education", "skills", "projects"]:
        if name in headers_found:
            score += per_header
            details.append(f"'{name.capitalize()}' section header detected.")
        else:
            details.append(f"'{name.capitalize()}' section header not found.")

    return {"score": min(score, max_score), "max": max_score, "details": details}


def _find_matched_skills(text_lower):
    """Match skill keywords using boundary-aware regex so short keywords
    (e.g. 'java') don't false-positive match inside longer ones (e.g.
    'javascript')."""
    matched = []
    for skill in COMMON_SKILLS:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            matched.append(skill)
    return matched


def _score_skills(text_lower, headers_found):
    max_score = 20
    score = 0
    details = []

    if "skills" in headers_found:
        score += 5
        details.append("Dedicated skills section found.")
    else:
        details.append("No dedicated skills section found.")

    matched_skills = _find_matched_skills(text_lower)
    score += min(len(matched_skills), 15)

    if matched_skills:
        preview = ", ".join(matched_skills[:5])
        details.append(f"{len(matched_skills)} recognizable skill keyword(s) found (e.g. {preview}).")
    else:
        details.append("No recognizable technical or soft skill keywords found.")

    return {"score": min(score, max_score), "max": max_score, "details": details}


def _score_projects(text, text_lower, headers_found):
    max_score = 20
    score = 0
    details = []

    if "projects" not in headers_found:
        details.append("No projects section found.")
        return {"score": score, "max": max_score, "details": details}

    score += 5
    details.append("Projects section found.")

    # Isolate the projects section (from its header to the next major
    # header, or end of document) so entries are only counted within it.
    match = re.search(r"projects?\b", text_lower)
    section_text = text[match.start():] if match else ""
    next_header_match = re.search(
        r"\n\s*(experience|education|skills|certifications|summary)\b",
        section_text[10:], re.IGNORECASE,
    )
    if next_header_match:
        section_text = section_text[:10 + next_header_match.start()]

    bullets = BULLET_PATTERN.findall(section_text)
    lines = [ln for ln in section_text.split("\n") if ln.strip()]
    entry_estimate = max(len(bullets), max(0, len(lines) - 1))
    score += min(entry_estimate, 3) * 5

    if entry_estimate > 0:
        details.append(f"Approximately {entry_estimate} project entry line(s) detected.")
    else:
        details.append("Projects section found but appears to contain little content.")

    return {"score": min(score, max_score), "max": max_score, "details": details}


def _score_education(text_lower, headers_found):
    max_score = 15
    score = 0
    details = []

    if "education" in headers_found:
        score += 5
        details.append("Education section found.")
    else:
        details.append("No education section found.")

    if any(re.search(p, text_lower) for p in DEGREE_KEYWORDS):
        score += 5
        details.append("Degree keyword found (e.g. Bachelor's, Master's, B.Tech).")
    else:
        details.append("No recognizable degree keyword found.")

    if any(re.search(p, text_lower) for p in INSTITUTION_KEYWORDS):
        score += 5
        details.append("Institution name or GPA/percentage detail found.")
    else:
        details.append("No institution name or GPA/percentage detail found.")

    return {"score": min(score, max_score), "max": max_score, "details": details}


def _score_completeness(text, headers_found):
    max_score = 15
    score = 0
    details = []

    word_count = len(text.split())
    if word_count >= 300:
        score += 5
        details.append(f"Resume length is solid ({word_count} words).")
    elif word_count >= 150:
        score += 3
        details.append(f"Resume length is a bit short ({word_count} words).")
    else:
        details.append(f"Resume is very short ({word_count} words) — likely incomplete.")

    if len(headers_found) >= 4:
        score += 5
        details.append(f"{len(headers_found)} distinct resume sections detected.")
    elif len(headers_found) >= 2:
        score += 3
        details.append(f"Only {len(headers_found)} distinct resume sections detected.")
    else:
        details.append("Very few distinct resume sections detected.")

    if BULLET_PATTERN.search(text):
        score += 5
        details.append("Bullet points used for formatting.")
    else:
        details.append("No bullet points detected — consider using them for readability.")

    return {"score": min(score, max_score), "max": max_score, "details": details}


def score_resume(text):
    """
    Score a resume's extracted text across six rule-based categories.
    Returns {"total_score": int (0-100), "categories": {...}}.
    Handles empty/missing text gracefully (returns an all-zero score).
    """
    text = text or ""
    text_lower = text.lower()
    headers_found = _find_section_headers(text_lower)

    categories = {
        "contact_info": _score_contact_info(text, text_lower),
        "structure": _score_structure(headers_found),
        "skills": _score_skills(text_lower, headers_found),
        "projects": _score_projects(text, text_lower, headers_found),
        "education": _score_education(text_lower, headers_found),
        "completeness": _score_completeness(text, headers_found),
    }

    total_score = sum(cat["score"] for cat in categories.values())
    return {"total_score": total_score, "categories": categories}
