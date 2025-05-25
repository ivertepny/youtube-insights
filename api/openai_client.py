# api/openai_client.py
import os
from openai import OpenAI

class OpenAIClient:
    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_insight(self, title, description):
        prompt = (
            "You are a YouTube content analyst. Based on the title and description below, "
            "explain in 1–2 sentences why this video might be performing well, focusing on emotional hook, clarity, or unique topic.\n\n"
            f"Title: {title}\n\n"
            f"Description: {description}\n\n"
            "Insight:"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating insight: {str(e)}"
