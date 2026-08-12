ALLOWED_DOMAINS = [
    "gmail.com",
    "opentrends.com",
    "opentrends.net",
    "fifa-scoring.com",
]


def validate_email_domain(email: str | None) -> str | None:
    if not email:
        return None
    email_lower = email.strip().lower()
    domain = email_lower.split("@")[-1] if "@" in email_lower else ""
    if domain not in ALLOWED_DOMAINS:
        return "Email domain not allowed. Use Gmail, OpenTrends, or FIFA Scoring email."
    return None
