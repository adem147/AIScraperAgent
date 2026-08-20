from .nvidia_client import generate_json

SYSTEM_PROMPT = """
You are an information extraction system.

Extract structured public procurement data from text.

Rules:
- Output ONLY valid JSON
- Do not add explanations
- If a field is missing, return null
- Use ISO format for dates (YYYY-MM-DD)

TARGET SCHEMA:
{
  "title": null,
  "description": null,
  "url": null,
  "published_date": null,
  "submission_deadline",null,
  "sector": null,
  "contry":null
}

MAPPING GUIDELINES:
- "title": field representing the main object (what is being procured)
- "description": field containing descriptive or detailed text
- "submission_deadline": field containing a closing or deadline date
- "published_date": field representing publication date, release date, or announcement date
- "url": field containing a URL or link
- "sector": field representing category, domain, or industry
- "country": field representing the country where the project or procurement is located or assigned
"""


def extract_from_text(text, source_name=None, source_url=None, notice_id=None):
    """Extract structured procurement entities from raw text."""
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    prompt = f"""
    TEXT:
    {text.strip()}
    """
    
    return generate_json(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=1024,
    )
