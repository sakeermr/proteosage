"""
services/llm_service.py - Fixed version
"""
import logging
import os

logger = logging.getLogger(__name__)


def _get_secret(key: str) -> str:
    try:
        import streamlit as st
        val = st.secrets[key]
        if val:
            return str(val).strip()
    except Exception:
        pass
    return os.environ.get(key, "").strip()


class LLMService:

    def complete(self, system_prompt: str, user_prompt: str,
                 temperature: float = 0.3, max_tokens: int = 1500) -> str:

        openai_key = _get_secret("OPENAI_API_KEY")
        gemini_key = _get_secret("GEMINI_API_KEY")
        model = _get_secret("LLM_MODEL") or "gpt-4o-mini"

        # Try OpenAI
        if openai_key and openai_key.startswith("sk-"):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error("OpenAI error: %s", e)
                return f"OpenAI error: {str(e)[:200]}"

        # Try Gemini
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                m = genai.GenerativeModel("gemini-1.5-flash")
                response = m.generate_content(f"{system_prompt}\n\n{user_prompt}")
                return response.text.strip()
            except Exception as e:
                logger.error("Gemini error: %s", e)
                return f"Gemini error: {str(e)[:200]}"

        return f"No valid API key. Key starts with: {openai_key[:10] if openai_key else 'EMPTY'}"


llm_service = LLMService()