import json
import requests
import os
import sys

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = "llama3.2:3b"   # change if you have a different model

def call_ollama(prompt, max_retries=3):
    """
    Send a prompt to Ollama and return the response text.
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,   # keep deterministic
            "num_predict": 2048
        }
    }
    for attempt in range(max_retries):
        try:
            resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}", file=sys.stderr)
            if attempt == max_retries - 1:
                raise
    return ""

def extract_json_from_llm_output(text):
    """
    Try to parse JSON from LLM output (handles markdown code blocks).
    """
    # Remove markdown code fences if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)