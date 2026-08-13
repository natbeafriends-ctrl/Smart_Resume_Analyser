"""
feedback.py
-----------
Rule-based Smart Feedback System (Module 4).

Pulls together signals already computed by Module 2 (score breakdown) and
Module 3 (ATS keyword gaps), plus two additional rule-based checks not
covered by either earlier module (certifications, internship experience),
and turns all of it into a short, prioritized list of improvement
suggestions — the "recommendation logic" / "decision-making workflow"
layer the capstone spec asks for.

No ML/LLM calls: every suggestion is triggered by a specific, explainable
rule against the resume text and/or the Module 2/3 output. Nothing here
re-derives scoring or keyword logic — it consumes score_resume()'s and
check_ats()'s output directly so the three modules stay in sync.
"""

from utils import keyword_in_text

CERTIFICATION_KEYWORDS = ["certified", "certification", "certificate", "credential"]
INTERNSHIP_KEYWORDS = ["intern", "internship", "trainee"]

# Lower number = shown first. Ties broken by insertion order.
PRIORITY_FORMATTING = 1
PRIORITY_CONTENT = 2
PRIORITY_KEYWORDS = 2
PRIORITY_CREDENTIALS = 3


def _has_any(keywords, text_lower):
    return any(keyword_in_text(kw, text_lower) for kw in keywords)


def generate_feedback(text, score_result=None, ats_result=None, max_suggestions=8):
    """
    Build a prioritized list of improvement suggestions.

    Args:
        text: the resume's extracted text.
        score_result: optional dict as returned by scorer.score_resume().
            When provided, weak Module 2 categories (formatting/structure,
            projects) feed suggestions.
        ats_result: optional dict as returned by ats_checker.check_ats().
            When provided, missing role keywords feed suggestions.
        max_suggestions: cap on how many suggestions to return.

    Returns:
        [{"suggestion": str, "category": str, "priority": int}, ...]
        sorted by priority (1 = most important), capped at max_suggestions.
        Returns an empty list if nothing needs improving.
    """
    text = text or ""
    text_lower = text.lower()
    suggestions = []  # list of (priority, category, suggestion_text)

    if score_result:
        categories = score_result.get("categories", {})

        completeness = categories.get("completeness", {})
        if completeness.get("score", 0) < completeness.get("max", 15):
            details_lower = " ".join(completeness.get("details", [])).lower()
            if "no bullet points detected" in details_lower:
                suggestions.append((
                    PRIORITY_FORMATTING, "Formatting",
                    "Improve resume formatting — use bullet points to highlight achievements.",
                ))
            if "very short" in details_lower or "a bit short" in details_lower:
                suggestions.append((
                    PRIORITY_FORMATTING, "Formatting",
                    "Improve resume formatting — the resume is short; add more detail on your experience.",
                ))

        structure = categories.get("structure", {})
        missing_sections = [
            d.split("'")[1] for d in structure.get("details", [])
            if d.lower().endswith("not found.")
        ]
        if missing_sections:
            suggestions.append((
                PRIORITY_FORMATTING, "Formatting",
                f"Improve resume formatting — add a clear {', '.join(missing_sections)} section.",
            ))

        projects = categories.get("projects", {})
        if projects.get("score", 0) < projects.get("max", 20):
            suggestions.append((
                PRIORITY_CONTENT, "Projects",
                "Add technical projects that demonstrate hands-on skills relevant to your target role.",
            ))

    if not _has_any(CERTIFICATION_KEYWORDS, text_lower):
        suggestions.append((
            PRIORITY_CREDENTIALS, "Credentials",
            "Include certifications relevant to your field to strengthen your profile.",
        ))

    if not _has_any(INTERNSHIP_KEYWORDS, text_lower):
        suggestions.append((
            PRIORITY_CREDENTIALS, "Experience",
            "Add internship experience, if you have any relevant hands-on experience.",
        ))

    if ats_result:
        for suggestion_text in ats_result.get("suggestions", [])[:4]:
            suggestions.append((PRIORITY_KEYWORDS, "Keywords", suggestion_text))

    # De-duplicate identical suggestion text, keeping the best (lowest) priority.
    seen = {}
    for priority, category, suggestion_text in suggestions:
        if suggestion_text not in seen or priority < seen[suggestion_text][0]:
            seen[suggestion_text] = (priority, category)

    deduped = [
        {"suggestion": suggestion_text, "category": category, "priority": priority}
        for suggestion_text, (priority, category) in seen.items()
    ]
    deduped.sort(key=lambda s: s["priority"])

    return deduped[:max_suggestions]
