import re

LEGAL_SUFFIX_PATTERN = re.compile(
    r"\b(llc|ltd|limited|inc|incorporated|corp|corporation|gmbh)\.?\b",
    flags=re.IGNORECASE,
)
SPACE_PATTERN = re.compile(r"\s+")


def normalize_company_name(name: str) -> str:
    cleaned = LEGAL_SUFFIX_PATTERN.sub("", name)
    cleaned = re.sub(r"[,\.\-]+$", "", cleaned)
    cleaned = SPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned

