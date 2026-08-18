import json
import re


KEYWORDS = [
    "opportunity", "opportunities",
    "tender", "tenders",
    "procurement",
    "notice",
    "result",
    "data",
    "items",
    "results",
]

AMIAO_KEYWORDS = [
    "appel", "tender", "EOI", "AMI", "AO",
    "expression", "interest", "consulting"
]

def parse_json_response(response):
    """Safely parse a Playwright response body as JSON when possible."""
    content_type = response.headers.get("content-type", "").lower()
    body_text = response.text()

    if not body_text:
        return None

    if "json" not in content_type and not body_text.lstrip().startswith(("{", "[")):
        return None

    try:
        return json.loads(body_text)
    except Exception as exc:
        print(f"Couldn't parse JSON from {response.url}: {exc}")
        return None


def get_middle_response_items(data, limit=5):
    """Return up to five meaningful items from the middle of a JSON response."""
    if data is None:
        return []

    if isinstance(data, list):
        if not data:
            return []
        if len(data) <= limit:
            return data

        start = max(0, len(data) // 2 - limit // 2)
        return data[start:start + limit]

    if isinstance(data, dict):
        values = list(data.values())
        if not values:
            return []
        if len(values) <= limit:
            return values

        start = max(0, len(values) // 2 - limit // 2)
        return values[start:start + limit]

    return [data]


def create_sample_text(data, max_chars=1200):
    """Flatten the selected middle sample items of a JSON response into a short sample."""
    items = get_middle_response_items(data)

    if not items:
        return ""

    sample_parts = []
    for item in items:
        if isinstance(item, dict):
            for key, value in list(item.items())[:8]:
                value_text = create_sample_text(value, max_chars=200)
                if value_text:
                    sample_parts.append(f"{key}: {value_text}")
        elif isinstance(item, list):
            nested_text = create_sample_text(item, max_chars=200)
            if nested_text:
                sample_parts.append(nested_text)
        elif isinstance(item, str):
            item_text = item.strip()
            if item_text:
                sample_parts.append(item_text)
        else:
            item_text = str(item)
            if item_text:
                sample_parts.append(item_text)

    text = " ".join(sample_parts)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def is_relevant_text(text: str) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in AMIAO_KEYWORDS)


def score_node(node: Any) -> int:
    score = 0
    text = str(node).lower()

    # keyword score
    score += sum(1 for k in KEYWORDS if k in text)

    # AMI/AO score
    score += sum(2 for k in AMIAO_KEYWORDS if k in text)

    # structure score
    if isinstance(node, dict):
        score += len(node.keys())

    if isinstance(node, list):
        score += len(node)

    if "http" in text:
        score += 3

    if re.search(r"\d{4}|\d{2}/\d{2}", text):
        score += 1

    return score

def extract_candidates(obj: Any, depth: int = 0, max_depth: int = 10):
    candidates = []

    if depth > max_depth:
        return candidates

    if isinstance(obj, dict):
        # if dict looks like a full opportunity
        candidates.append(obj)

        for k, v in obj.items():
            candidates.extend(extract_candidates(v, depth + 1))

    elif isinstance(obj, list):
        for item in obj:
            candidates.extend(extract_candidates(item, depth + 1))

    return candidates

#Main function extractor fonction
def universal_json_extractor(json_data: Union[dict, list], top_k: int = 1):
    candidates = extract_candidates(json_data)

    scored = [(score_node(c), c) for c in candidates]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [c for _, c in scored[:top_k]]

