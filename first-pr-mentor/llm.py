"""LLM layer: any OpenAI-compatible endpoint, configured only by env vars
LLM_BASE_URL, LLM_API_KEY, LLM_MODEL. Keys are never printed or logged."""
import json
import os
import re

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMError(Exception):
    """Friendly, user-facing LLM error."""


def _client():
    base_url, model = os.getenv("LLM_BASE_URL"), os.getenv("LLM_MODEL")
    if not base_url or not model:
        raise LLMError("The AI model isn't configured. Set LLM_BASE_URL and LLM_MODEL in your .env file (see .env.example).")
    # Local servers like Ollama ignore the key but the client needs a non-empty one
    return OpenAI(base_url=base_url, api_key=os.getenv("LLM_API_KEY") or "not-needed", timeout=180), model


def _extract_json(text):
    """Strip markdown fences and parse the first {...} block. Raises ValueError if invalid."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.I)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])


@st.cache_data(ttl=3600, show_spinner=False)
def chat_json(system, user):
    """Ask the model for JSON. Temperature 0.2. Retries once if the JSON is invalid."""
    client, model = _client()
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    for _ in range(2):
        try:
            resp = client.chat.completions.create(model=model, messages=messages, temperature=0.2)
        except Exception:
            raise LLMError("Couldn't reach the AI model. Is Ollama running, and are LLM_BASE_URL / LLM_API_KEY / LLM_MODEL correct?") from None
        text = resp.choices[0].message.content or ""
        try:
            return _extract_json(text)
        except ValueError:  # includes json.JSONDecodeError
            messages = messages + [
                {"role": "assistant", "content": text},
                {"role": "user", "content": "That was not valid JSON. Reply again with ONLY the JSON object and nothing else."},
            ]
    raise LLMError("The AI model didn't return valid JSON. Try again, or use a stronger model.")
