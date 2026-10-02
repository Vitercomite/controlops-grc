"""Small presentation helpers shared by pages."""
ICON = {
    "PASS": "🟢 PASS", "FAIL": "🔴 FAIL", "PENDING": "🟡 PENDING",
    "OPEN": "🔴 OPEN", "IN_REMEDIATION": "🟠 IN_REMEDIATION",
    "READY_FOR_RETEST": "🔵 READY_FOR_RETEST", "CLOSED": "🟢 CLOSED",
    "LOW": "LOW", "MEDIUM": "🟡 MEDIUM", "HIGH": "🟠 HIGH", "CRITICAL": "🔴 CRITICAL",
}


def badge(value: str) -> str:
    return ICON.get(value, value)
