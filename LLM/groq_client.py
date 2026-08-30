import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def ask_groq(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """Simple Groq call used by the NLP extractor and mapper."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    client = Groq(api_key=api_key)
    model = "qwen/qwen3.8-27b"

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=1000,
    )

    return completion.choices[0].message.content