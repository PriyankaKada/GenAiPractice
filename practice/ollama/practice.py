from openai import OpenAI

# Point to your local Ollama server
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Ollama doesn't require a real key, but a placeholder string is needed
)

response = client.chat.completions.create(
    model="llama3.1:8b ",  # Must match the model you downloaded via Ollama
    messages=[{"role": "user", "content": "Hello! Do you know who is dinesh jadhav?"}]
)

print(response.choices[0].message.content)
