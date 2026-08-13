"""
utils.py
--------
Small shared helpers used across multiple rule-based modules
(scorer.py - Module 2, ats_checker.py - Module 3).
"""

import re


def keyword_in_text(keyword, text_lower):
    """Boundary-aware keyword check: True if `keyword` appears in
    `text_lower` as a whole token, not as a substring inside a longer word
    (e.g. 'java' should not match inside 'javascript'). `text_lower` is
    expected to already be lowercased by the caller."""
    pattern = r"(?<![a-zA-Z0-9])" + re.escape(keyword) + r"(?![a-zA-Z0-9])"
    return re.search(pattern, text_lower) is not None
