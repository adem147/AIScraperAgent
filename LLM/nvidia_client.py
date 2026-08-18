import os
import json
import requests
from dotenv import load_dotenv
#from ..scraper.json_parser import parse_json_response

load_dotenv()

API_KEY = os.getenv("NVIDIA_API_KEY")
if not API_KEY:
    raise ValueError("NVIDIA_API_KEY not in .env")

BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "meta/llama-3.1-8b-instruct"


def chat_completion(messages, temperature=0.1, max_tokens=2048):
    """Call NVIDIA API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    try:
        resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        print(f"NVIDIA API error: {e}")
        return ""


def generate_json(prompt, system_prompt, max_tokens=2048) -> dict:
    """Generate JSON from prompt."""

    if(system_prompt is None):
        print("System prompt cannot be None.")
        return {}
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    text = chat_completion(messages, temperature=0.05, max_tokens=max_tokens)
    
    if not text:
        return {}
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON: {text}")
        return {}
