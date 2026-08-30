import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from .groq_client import ask_groq


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# for model in client.models.list():
   # print(model.name)


def ask_llm(prompt):
    print("LLM processing opportunity ...")

    if os.getenv("GROQ_API_KEY"):
        return ask_groq(prompt)

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
            max_output_tokens=1000
        )
    )
    return response.text


import ollama


def ask_ollama(prompt, context):
    response = ollama.chat(
        model='gemma3:4b',
        messages=[
            {
                "role": "system",
                "content": f"You are an assistant. Use the following context to answer:\n\n{context}"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response['message']['content']

