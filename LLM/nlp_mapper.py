
import json

from LLM.nvidia_client import generate_json


SYSTEM_PROMPT = """
You are a JSON schema mapping system.

Your task is to map fields from an INPUT JSON object to a TARGET SCHEMA.

CRITICAL RULES:
- Output ONLY raw JSON
- Do NOT include explanations or markdown
- Keep the descrition short not more than one line 
- The output must start with { and end with }
- Keys MUST be the TARGET SCHEMA fields
- Values MUST be INPUT JSON FIELD NAMES (keys), NOT their values
- Do NOT invent field names
- If no match exists, return null

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

IMPORTANT:
- Analyze BOTH field names and their values to determine meaning
- Choose the BEST matching field for each schema entry
"""

def extract_from_json(json_data:list, source_name=None, source_url=None, notice_id=None):
    """Extract structured procurement entities from JSON data."""
    if not json_data:
        raise ValueError("Input JSON data cannot be empty.")

    prompt = f"""
    JSON DATA:
    {json.dumps(json_data[0], ensure_ascii=False)}
    """

    #print("extract_from_json prompt:", prompt)
        
    mapper = generate_json(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=2048,
    )

    #to be used for renaming the columns in the dataframe
    reverse_mapper = {
        v: k for k, v in mapper.items()
        if v is not None 
    }   

    return reverse_mapper