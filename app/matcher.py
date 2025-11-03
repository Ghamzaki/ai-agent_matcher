from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz
from datetime import datetime
import json

HIGH_SCORE = 85.0
LOW_SCORE = 50.0

def amount_score(parsed_amount: float, tx_amount: float) -> float:
    if parsed_amount is None:
        return 0.0
    if parsed_amount == tx_amount:
        return 100.0
    diff = abs(parsed_amount - tx_amount)
    denom = max(abs(tx_amount), 1.0)
    pct = diff / denom
    score = max(0.0, 100.0 - (pct * 500.0))
    return float(score)

def date_score(parsed_dt: Optional[datetime], tx_dt: Optional[datetime]) -> float:
    if not parsed_dt or not tx_dt:
        return 0.0
    delta = abs((parsed_dt - tx_dt).total_seconds())
    if delta < 60*5:
        return 100.0
    if delta < 60*60:
        return 80.0
    if delta < 60*60*6:
        return 50.0
    return max(0.0, 30.0 - (delta / (60*60*24)))

def merchant_score(parsed_merchant: Optional[str], tx_merchant: Optional[str]) -> float:
    if not parsed_merchant or not tx_merchant:
        return 0.0
    return float(fuzz.token_set_ratio(parsed_merchant, tx_merchant))

def combined_score(parsed: Dict[str,Any], tx: Dict[str,Any]) -> float:
    w_ref = 0.5
    w_amount = 0.3
    w_date = 0.1
    w_merchant = 0.1
    score_ref = 0.0
    if parsed.get("reference") and tx.get("metadata"):
        try:
            meta = json.loads(tx.get("metadata") or "{}")
            tx_ref = meta.get("reference")
            if tx_ref and tx_ref == parsed.get("reference"):
                score_ref = 100.0
        except:
            score_ref = 0.0

    score_amount = amount_score(parsed.get("amount"), tx.get("amount"))
    score_date = date_score(parsed.get("received_at"), tx.get("timestamp"))
    score_merchant = merchant_score(parsed.get("merchant"), tx.get("merchant"))

    combined = (
        (score_ref * w_ref) +
        (score_amount * w_amount) +
        (score_date * w_date) +
        (score_merchant * w_merchant)
    )
    return float(combined)

def choose_best(parsed: Dict[str,Any], candidates: List[Dict[str,Any]]) -> Dict[str,Any]:
    scored = []
    for tx in candidates:
        sc = combined_score(parsed, tx)
        scored.append({"tx": tx, "score": sc})
    scored.sort(key=lambda x: x["score"], reverse=True)
    if not scored:
        return {"status":"no_match", "best": None, "candidates": []}
    best = scored[0]
    if best["score"] >= HIGH_SCORE:
        return {"status":"matched", "best": best, "candidates": scored}
    elif best["score"] >= LOW_SCORE:
        return {"status":"ambiguous", "best": best, "candidates": scored}
    else:
        return {"status":"no_match", "best": best, "candidates": scored}