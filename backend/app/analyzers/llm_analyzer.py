import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMAnalyzer:
    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = "llama-3.3-70b-versatile"

    def explain_dead_code(self, code: str, dead_items: list) -> list:
        if not dead_items:
            return []

        explained = []
        for item in dead_items:
            explanation = self._get_explanation(code, item)
            item["ai_explanation"] = explanation
            item["fix_suggestion"] = self._get_fix(code, item)
            explained.append(item)
        return explained

    def _get_explanation(self, code: str, item: dict) -> str:
        try:
            lines = code.splitlines()
            start = max(0, item["line_start"] - 1)
            end = min(len(lines), item["line_end"])
            snippet = "\n".join(lines[start:end])

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this dead code snippet and explain in 2-3 sentences WHY it is dead/unused and what impact it has:

Code snippet (lines {item['line_start']}-{item['line_end']}):
{snippet}

Issue: {item['message']}

Give a concise technical explanation."""
                }]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"

    def _get_fix(self, code: str, item: dict) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": f"""For this dead code issue: "{item['message']}"
Type: {item['type']}

Give ONE short recommendation: should it be deleted, refactored, or kept? Why? Max 2 sentences."""
                }]
            )
            return response.choices[0].message.content
        except Exception as e:
            return "Delete this dead code to reduce complexity."