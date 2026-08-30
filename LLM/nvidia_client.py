import os
import json
import requests
from dotenv import load_dotenv
#from ..scraper.json_parser import parse_json_response

load_dotenv()

API_KEY = os.getenv("NVIDIA_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "deepseek-ai/deepseek-v4-flash-0731"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")


def _ollama_completion(messages, temperature=0.1, max_tokens=2048):
    """Use the local Ollama server when the NVIDIA API is unavailable."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "").strip()


def chat_completion(messages, temperature=0.1, max_tokens=2048):
    """Call NVIDIA API, then fall back to the local Ollama server."""
    if not API_KEY:
        print("NVIDIA_API_KEY is missing; trying Ollama.")
    else:
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
            resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if text:
                return text
            print("NVIDIA returned an empty response;")
        except Exception as error:
            print(f"NVIDIA API error: {error};")

    return ""

    headers = {
        "Content-Type": "application/json",
    }
    try:
        return _ollama_completion(messages, temperature, max_tokens)
    except Exception as error:
        print(f"Ollama fallback error: {error}")
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


class NvidiaLLMClient:
    """Compatibility client used by the extraction and analysis services."""

    def generate_json(self, prompt, system_prompt=None, max_tokens=2048):
        return generate_json(prompt, system_prompt, max_tokens)


def get_nvidia_client():
    return NvidiaLLMClient()
