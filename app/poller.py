import os, json
from datetime import datetime, timedelta
from typing import List, Dict,Any
from .db import get_session
from .models import Transaction
from sqlmodel import select

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "sample_data", "sample_transactions.json")

def load_sample_transactions() -> List[Dict[str,Any]]:
    with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def refresh_transactions_from_sample():
    data = load_sample_transactions()
    sess = get_session()
    for tx in data:
        obj = Transaction(
            id=tx["id"],
            timestamp=datetime.fromisoformat(tx["timestamp"]),
            account_masked=tx.get("account_masked"),
            merchant=tx.get("merchant"),
            amount=float(tx["amount"]),
            currency=tx.get("currency","NGN"),
            metadata=json.dumps(tx.get("metadata", {})),
            is_simulated=tx.get("is_simulated", True)
        )
        existing = sess.get(Transaction, obj.id)
        if not existing:
            sess.add(obj)
    sess.commit()
    sess.close()

def get_recent_transactions(window_hours=24) -> List[Dict[str,Any]]:
    sess = get_session()
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    stmt = select(Transaction).where(Transaction.timestamp >= cutoff)
    rows = sess.exec(stmt).all()
    result = []
    for r in rows:
        result.append({
            "id": r.id,
            "timestamp": r.timestamp,
            "account_masked": r.account_masked,
            "merchant": r.merchant,
            "amount": r.amount,
            "currency": r.currency,
            "metadata": r.metadata
        })
    sess.close()
    return result