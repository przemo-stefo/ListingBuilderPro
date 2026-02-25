# backend/utils/privacy.py
# Purpose: GDPR-compliant helpers — hash PII before storage
# NOT for: Authentication, authorization, or encryption of secrets

import hashlib
from config import settings


def hash_ip(ip: str) -> str:
    """Hash IP address with a server-side salt for GDPR compliance.

    WHY: Raw IPs are PII under GDPR. Hashing preserves rate-limiting
    (same IP → same hash) while preventing IP reconstruction from DB dumps.
    WHY salt: Prevents rainbow table attacks on the limited IPv4 space.
    """
    salt = (settings.api_secret_key or "fallback-salt")[:16]
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:32]
