import os, httpx
from .config import settings

async def enrich_with_gemini(prompt: str):
    if not settings.GEMINI_API_KEY:
        return None
    # Placeholder: call Gemini REST API — user must provide actual endpoint/auth per their key
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{url}?key={settings.GEMINI_API_KEY}", json=payload, headers=headers)
        if r.status_code != 200:
            return None
        return r.json()