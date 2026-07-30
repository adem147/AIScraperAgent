import json
import re


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
