import requests
import json
from datetime import datetime
from .config import settings


def fetch_mailtrap_messages():
    """
    Simulate fetching emails using the Mailtrap Sandbox API.
    (Mailtrap Sandbox only supports sending test emails; this mock simulates the inbox.)
    """

    url = f"{settings.MAILTRAP_API_URL}/{settings.MAILTRAP_INBOX_ID}"
    headers = {
        "Authorization": f"Bearer {settings.MAILTRAP_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Compose a mock test email
    payload = {
        "from": {"email": "noreply@bank.com", "name": "Demo Bank Alerts"},
        "to": [{"email": "demo@telex.local"}],
        "subject": "Bank Alert: Transaction at STARBUCKS $5.75",
        "text": (
            "Dear Customer,\n\n"
            "Your account was just charged $5.75 at STARBUCKS on 2025-11-03.\n"
            "If this wasn’t you, please contact us immediately.\n\n"
            "– Demo Bank"
        ),
        "category": "Transaction Alerts"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent test email to Mailtrap Sandbox successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send test email to Mailtrap Sandbox: {e}")

    # Simulated return payload (normally this would come from IMAP or Mailtrap API)
    return [{
        "subject": payload["subject"],
        "sender": payload["from"]["email"],
        "body": payload["text"],
        "timestamp": datetime.now().isoformat()
    }]


if __name__ == "__main__":
    messages = fetch_mailtrap_messages()
    print(f"Fetched {len(messages)} test messages.")