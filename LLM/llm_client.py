import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# for model in client.models.list():
   # print(model.name)

def ask_llm(prompt):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
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

