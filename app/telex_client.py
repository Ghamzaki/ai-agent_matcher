import os, httpx, json
from .config import settings

async def send_telex_message(channel_id: str, title: str, body: str, meta: dict = None):
    if not settings.TELEX_WEBHOOK_URL:
        print("TELEX MOCK SEND:", channel_id, title, body, meta)
        return {"ok": True, "mock": True}
    headers = {"Content-Type": "application/json"}
    if settings.TELEX_API_TOKEN:
        headers["Authorization"] = f"Bearer {settings.TELEX_API_TOKEN}"
    payload = {"channel_id": channel_id, "title": title, "body": body, "metadata": meta or {}}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(settings.TELEX_WEBHOOK_URL, json=payload, headers=headers)
        r.raise_for_status()
        try:
            return r.json()
        except:
            return {"ok": True, "status_code": r.status_code, "text": r.text}
    