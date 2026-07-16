import re
import unicodedata


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"([!?。！？])\1+", r"\1", normalized)
    return normalized

