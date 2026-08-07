import ollama

model_name = "gemma3:4b"

response = ollama.chat(
    model=model_name,
    messages=[
        {"role": "user", "content": "hi"}
    ]
)

print(response['message']['content'])