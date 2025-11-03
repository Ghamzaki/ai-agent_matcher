import asyncio, email, time, os
from aioimaplib import aioimaplib
from .config import settings
from .main import ingest_email_payload  # function we expose to handle an incoming parsed email
from email.header import decode_header
from .email_parser import parse_email

async def fetch_and_process():
    host = settings.IMAP_HOST
    port = settings.IMAP_PORT
    user = settings.IMAP_USER
    password = settings.IMAP_PASS
    use_ssl = settings.IMAP_USE_SSL
    if not host or not user or not password:
        print("IMAP not configured; skipping mail fetch")
        return
    try:
        client = aioimaplib.IMAP4_SSL(host, port) if use_ssl else aioimaplib.IMAP4(host, port)
        await client.wait_hello_from_server()
        await client.login(user, password)
        await client.select("INBOX")
        # search unseen
        resp = await client.search("UNSEEN")
        if resp.lines and resp.lines[0]:
            ids = resp.lines[0].split()
            for id_ in ids:
                fetch_resp = await client.fetch(id_, "(RFC822)")
                raw = b"".join(fetch_resp.lines[1:-1])
                msg = email.message_from_bytes(raw)
                subject = decode_header(msg.get("Subject"))[0][0]
                if isinstance(subject, bytes):
                    try:
                        subject = subject.decode()
                    except:
                        subject = subject.decode("utf-8", "ignore")
                sender = msg.get("From")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        if ctype == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode()
                                break
                            except:
                                continue
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except:
                        body = ""
                payload = {
                    "subject": subject,
                    "sender": sender,
                    "body": body
                }
                
                # parse the email content into structured fields
                parsed = parse_email(payload)

                # now pass both raw + parsed data to the ingestion handler
                await ingest_email_payload(payload, parsed)
                # mark seen
                await client.store(id_, "+FLAGS", "\\Seen")
        await client.logout()
    except Exception as e:
        print("IMAP fetch error:", e)

async def start_imap_poller():
    interval = settings.IMAP_POLL_INTERVAL_SECONDS
    while True:
        await fetch_and_process()
        await asyncio.sleep(interval)