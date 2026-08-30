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


def _extract_message_text(message):
    """Extract a plain-text response from a message object or dictionary."""
    if message is None:
        return ""

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item:
                    parts.append(str(item["content"]))
                elif "value" in item:
                    parts.append(str(item["value"]))
            else:
                parts.append(str(item))
        return "".join(parts).strip()

    if content is None:
        return ""
    return str(content).strip()


def _extract_reasoning(message):
    """Extract reasoning metadata from NVIDIA/OpenAI-style responses."""
    if message is None:
        return ""

    for field_name in ("reasoning", "reasoning_content", "reasoning_text"):
        value = getattr(message, field_name, None)
        if value is None and isinstance(message, dict):
            value = message.get(field_name)
        if value:
            if isinstance(value, list):
                return "".join(str(item) for item in value).strip()
            if isinstance(value, dict):
                return json.dumps(value, ensure_ascii=False)
            return str(value).strip()

    return ""


def chat_completion_with_reasoning(messages, temperature=0.1, max_tokens=2048):
    """Call NVIDIA API and return both the final answer and its reasoning."""
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
            "stream": False,
            "extra_body": {
                "chat_template_kwargs": {
                    "thinking": True,
                    "reasoning_effort": "high",
                }
            },
        }

        try:
            resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = _extract_message_text(message)
            reasoning = _extract_reasoning(message)
            if content or reasoning:
                return {"content": content, "reasoning": reasoning}
            print("NVIDIA returned an empty response.")
        except Exception as error:
            print(f"NVIDIA API error: {error}")

    try:
        fallback = _ollama_completion(messages, temperature, max_tokens)
        return {"content": fallback, "reasoning": ""}
    except Exception as error:
        print(f"Ollama fallback error: {error}")
        return {"content": "", "reasoning": ""}


def chat_completion(messages, temperature=0.1, max_tokens=2048):
    """Backward-compatible content-only wrapper around the NVIDIA client."""
    result = chat_completion_with_reasoning(messages, temperature, max_tokens)
    return result.get("content", "")


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
