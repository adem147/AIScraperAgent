import os
import json
import re
import time
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

load_dotenv()

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"


class NvidiaLLMClient:
    """Client for NVIDIA Build API offering fast, lightweight LLM inference."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not set. Please add it to your .env file."
            )
        self.model = model
        self.base_url = NVIDIA_BASE_URL

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        retries: int = 3,
    ) -> str:
        """Execute a chat completion with retry logic."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9,
        }

        last_error = None
        for attempt in range(retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=45,
                )
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                    return ""
                elif response.status_code in [429, 500, 502, 503, 504]:
                    # Rate limit or temporary server error
                    time.sleep(1.5 * (attempt + 1))
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    continue
                else:
                    response.raise_for_status()
            except Exception as e:
                last_error = str(e)
                time.sleep(1.0 * (attempt + 1))

        raise RuntimeError(f"NVIDIA API call failed after {retries} attempts: {last_error}")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Send a prompt requesting strict JSON output and safely parse it."""
        default_system = (
            "You are an expert AI system for public procurement notice analysis. "
            "You always respond ONLY with valid JSON, without any conversational filler, markdown explanations, or code blocks."
        )
        sys_msg = system_prompt or default_system

        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt},
        ]

        raw_text = self.chat_completion(messages=messages, temperature=0.05, max_tokens=max_tokens)
        return self._clean_and_parse_json(raw_text)

    def _clean_and_parse_json(self, text: str) -> Dict[str, Any]:
        """Clean markdown code fences, trailing commas, and parse JSON safely."""
        if not text:
            return {}

        cleaned = text.strip()

        # Remove markdown codeblocks ```json ... ``` or ``` ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
            if match:
                cleaned = match.group(1).strip()
            else:
                cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

        # Try direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try to find the first '{' and the last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_substr = cleaned[start : end + 1]
            try:
                return json.loads(json_substr)
            except json.JSONDecodeError:
                # Fix trailing commas before } or ]
                fixed = re.sub(r",\s*([}\]])", r"\1", json_substr)
                try:
                    return json.loads(fixed)
                except Exception:
                    pass

        # Fallback: empty dict
        print(f"Warning: Failed to parse LLM response into JSON: {text[:200]}...")
        return {}


# Default singleton instance
_client: Optional[NvidiaLLMClient] = None

def get_nvidia_client() -> NvidiaLLMClient:
    global _client
    if _client is None:
        _client = NvidiaLLMClient()
    return _client
