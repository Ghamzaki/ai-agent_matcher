import re
from decimal import Decimal
from typing import Dict, Any, Optional
from rapidfuzz import fuzz

AMOUNT_RE = re.compile(r'([Nn]?₦|\bNGN\b|\$|\bUSD\b|\bEUR\b)?\s*([0-9]{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)')
REF_RE = re.compile(r'\bRef(?:erence)?[:\s]*([A-Z0-9\-]{4,30})\b', re.I)
TX_RE = re.compile(r'\bTx(?:n|nref)?[:\s]*([A-Z0-9\-]{4,30})\b', re.I)

def parse_amount(text: str) -> Optional[float]:
    m = AMOUNT_RE.search(text.replace(',', ''))
    if not m:
        return None
    amt = m.group(2)
    try:
        return float(Decimal(amt))
    except:
        try:
            return float(amt.replace(',', ''))
        except:
            return None

def parse_account_mask(text: str) -> Optional[str]:
    m = re.search(r'(\*\*\*+\s*\d{2,4})|(\d{4})', text)
    if m:
        candidate = m.group(1) or m.group(2)
        if candidate:
            return candidate.strip().replace(' ', '')
    return None

def parse_reference(text: str) -> Optional[str]:
    m = REF_RE.search(text) or TX_RE.search(text)
    return m.group(1) if m else None

def parse_merchant(text: str) -> Optional[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    subject_line = lines[0]
    subject_line = re.sub(r'(debit|credit|alert|notice|transaction|txn|ref)\b', '', subject_line, flags=re.I)
    short = subject_line[:80]
    return short.strip() if len(short) > 0 else None

def parse_email(raw: Dict[str, Any]) -> Dict[str, Any]:
    text = ' '.join(filter(None, [raw.get('subject',''), raw.get('body','')]))
    return {
        "amount": parse_amount(text),
        "currency": None,
        "account_masked": parse_account_mask(text),
        "reference": parse_reference(text),
        "merchant": parse_merchant(text),
    }