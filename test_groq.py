import os

from dotenv import load_dotenv
from LLM.groq_client import ask_groq

load_dotenv()

if __name__ == "__main__":
    prompt = "Say hello in one word."
    system_prompt = "You are a helpful assistant."

    if not os.getenv("GROQ_API_KEY"):
        print("Missing GROQ_API_KEY in environment.")
    else:
        try:
            result = ask_groq(prompt, system_prompt)
            print(result)
        except Exception as exc:
            print(f"Groq call failed: {type(exc).__name__}: {exc}")
