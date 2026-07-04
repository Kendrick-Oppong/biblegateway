"""
Mapping from BibleGateway version codes to human-readable names.
Used to create human-friendly folder names in the output.
"""
VERSION_NAMES = {
    # English
    "KJV": "King James Version",
    "AKJV": "Authorized King James Version",
    "KJ21": "21st Century King James Version",
    "NKJV": "New King James Version",
    "NIV": "New International Version",
    "NIVUK": "New International Version UK",
    "NIRV": "New International Reader's Version",
    "ESV": "English Standard Version",
    "ESVUK": "English Standard Version Anglicised",
    "NLT": "New Living Translation",
    "CSB": "Christian Standard Bible",
    "HCSB": "Holman Christian Standard Bible",
    "NASB": "New American Standard Bible",
    "NASB1995": "New American Standard Bible 1995",
    "AMP": "Amplified Bible",
    "AMPC": "Amplified Bible Classic",
    "MSG": "The Message",
    "GNT": "Good News Translation",
    "CEV": "Contemporary English Version",
    "CEB": "Common English Bible",
    "NRSVA": "New Revised Standard Version Anglicised",
    "NRSVACE": "NRSV Anglicised Catholic Edition",
    "NCV": "New Century Version",
    "NET": "New English Translation",
    "MEV": "Modern English Version",
    "LEB": "Lexham English Bible",
    "MOUNCE": "Mounce Reverse-Interlinear New Testament",
    "CJB": "Complete Jewish Bible",
    "GW": "GOD'S WORD Translation",
    "TLB": "Living Bible",
    "PHILLIPS": "J.B. Phillips New Testament",
    "JUB": "Jubilee Bible 2000",
    "ASV": "American Standard Version",
    "BARBY": "Darby Translation",
    "DLNT": "Disciples' Literal New Testament",
    "DRA": "Douay-Rheims 1899",
    "EHV": "Evangelical Heritage Version",
    "EXB": "Expanded Bible",
    "GNV": "1599 Geneva Bible",
    "BRG": "BRG Bible",
    "ICB": "International Children's Bible",
    "ISV": "International Standard Version",
    "NABRE": "New American Bible Revised Edition",
    "NCB": "New Catholic Bible",
    "NMB": "New Matthew Bible",
    "NOG": "Names of God Bible",
    "ERV": "Easy-to-Read Version",

    # Tagalog
    "ADB1905": "Ang Dating Biblia (1905)",
    "ABTAG1978": "Ang Biblia (1978)",
    "ABTAG2001": "Ang Biblia (2001)",
    "MBBTAG": "Magandang Balita Biblia",
    "MBBTAG-DC": "Magandang Balita Biblia (with Deuterocanon)",
    "ASND": "Ang Salita ng Diyos",
    "SND": "Ang Salita ng Diyos (SND)",  # unsure, but from code
    "FSV": "Ang Bagong Tipan",

    # Cebuano
    "APSD-CEB": "Ang Pulong Sa Dios (Cebuano)",

    # Ilonggo
    "HLGN": "Ang Pulong Sang Dios (Ilonggo)",
}

def sanitize_folder_name(name: str) -> str:
    """Replace characters that are unsafe for folder names."""
    # Remove leading/trailing spaces, replace slashes and colons
    # Keep spaces, letters, numbers, hyphens, underscores, parentheses.
    import re
    # Replace any sequence of invalid chars with a single underscore
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Collapse multiple spaces/underscores
    sanitized = re.sub(r'[ _]+', ' ', sanitized).strip()
    return sanitized
