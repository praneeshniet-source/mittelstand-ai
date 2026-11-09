
from analytics.ollama_client import ask_ollama

question = "Why is cash flow management important for a German SME?"

answer = ask_ollama(question)

print("\nQUESTION:")
print(question)

print("\nOLLAMA RESPONSE:")
print(answer)
