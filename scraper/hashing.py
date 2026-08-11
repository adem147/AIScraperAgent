# utils/hash_utils.py

import hashlib
import re
import unicodedata


def normalize_text(text: str) -> str:
    if not text:
        return ""

    # lowercase
    text = text.lower().strip()

    # remove accents (important for FR/AR mixed data)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text


def generate_hash(title: str, deadline: str, description: str) -> str:
    title = normalize_text(title)
    deadline = normalize_text(deadline)
    description = normalize_text(description)

    base_string = f"{title}|{deadline}|{description}"

    return hashlib.sha256(base_string.encode()).hexdigest()