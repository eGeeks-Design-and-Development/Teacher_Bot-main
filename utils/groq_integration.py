# utils/groq_integration.py

from groq import Groq

class GroqClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def get_groq_response(self, messages, model="llama-3.1-8b-instant", temperature=0.5, max_tokens=1024):
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            stream=False,
            stop=None,
        )

        response = ""
        for chunk in completion.choices:
            response += chunk.message.content

        return response
