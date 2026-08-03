import ollama

client = ollama.Client()
response = client.chat(
    model='llama3.1:8b',
    messages=[{'role': 'user', 'content': 'tell me a joke'}]
)
print(response['message']['content'])