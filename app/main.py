from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
import re
import json
from typing import List, Dict, Any
from rapidfuzz import fuzz
from .db import get_session
from .models import EmailAlert, MatchRun
from .poller import get_recent_transactions
from .matcher import choose_best
from datetime import datetime
import json
import uuid
import asyncio
from .email_reader_mailtrap import fetch_mailtrap_messages


# --- CONFIGURATION AND DATA SETUP ---

# Use a global dictionary to simulate the in-memory ledger database
TRANSACTION_LEDGER: Dict[str, Dict[str, Any]] = {}
ACCURACY_THRESHOLD = 0.80

# --- DATA MODELS ---

class PolledTransaction(BaseModel):
    """Represents a transaction pulled from the banking system via the 15-min poller."""
    tx_id: str
    amount: float
    description: str
    polled_at: datetime
    verified: bool = False

class AlertRequest(BaseModel):
    """The input payload representing the simulated bank alert email (The A2A Task)."""
    email_content: str

class AgentArtifact(BaseModel):
    """The structured output returned by the Agent (The A2A Artifact)."""
    status: str
    match_found: bool
    match_score: float
    alert_data: Dict[str, Any]
    matched_transaction: PolledTransaction | None
    message: str

# --- MOCK LEDGER GENERATION ---

def generate_mock_ledger(count: int = 5):
    """Fills the in-memory ledger with mock data, simulating the 15-minute poll."""
    global TRANSACTION_LEDGER
    mock_data = {
        "AMAZONPRCH": [50.99, 125.45],
        "STARBUCKS": [4.50, 6.75, 12.00],
        "UTILITYBILL": [75.00, 150.00],
        "GROCERYMART": [88.20, 45.10, 102.30],
        "REFUNDXYZ": [-20.00, -5.50],
    }

    TRANSACTION_LEDGER.clear()
    
    for i in range(count):
        description_key = random.choice(list(mock_data.keys()))
        amount = random.choice(mock_data[description_key])
        
        # Simulate recent polling times (within the last hour)
        poll_time = datetime.now() - timedelta(minutes=random.randint(1, 60))
        tx_id = f"TX{random.randint(10000, 99999)}"
        
        tx = PolledTransaction(
            tx_id=tx_id,
            amount=amount,
            description=description_key,
            polled_at=poll_time
        )
        TRANSACTION_LEDGER[tx_id] = tx.model_dump()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ledger Mocked/Polled with {len(TRANSACTION_LEDGER)} entries.")

# Initialize the ledger on startup
generate_mock_ledger()


# --- AGENT CORE FUNCTIONS ---

def parse_email_alert(email_text: str) -> Dict[str, Any]:
    """
    Simulates the AI agent's ability to parse key details from a natural language email.
    
    A strong agent would use an LLM for robust parsing, but here we use regex for stability.
    """
    alert_data = {"amount": None, "description": None, "date": None}

    # 1. Amount Parsing: Looks for dollar sign or currency followed by a number
    amount_match = re.search(r'[\$£€]\s*(\d+\.\d{2})|(\d+\.\d{2})\s*(USD|EUR|GBP)', email_text, re.IGNORECASE)
    if amount_match:
        # Prioritize the first capture group that holds the number
        num_str = amount_match.group(1) or amount_match.group(2)
        try:
            alert_data["amount"] = float(num_str)
        except (ValueError, TypeError):
            pass

    # 2. Description Parsing: Looks for merchant name or purchase details
    # Focuses on capitalized words near keywords like 'merchant', 'purchase', 'at'
    desc_match = re.search(r'(?:merchant|at|purchase from)\s+([A-Z\s]{4,})', email_text, re.IGNORECASE)
    if desc_match:
        # Clean and uppercase the description for comparison
        desc = desc_match.group(1).strip()
        desc = re.sub(r'\s+', ' ', desc).upper()
        # Keep only the first few words to avoid catching the rest of the email
        alert_data["description"] = " ".join(desc.split()[:3])
    
    # 3. Date Parsing: Looks for ISO date format (or similar)
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', email_text)
    if date_match:
        alert_data["date"] = date_match.group(0)

    return alert_data

def calculate_match_score(alert: Dict[str, Any], polled: Dict[str, Any]) -> float:
    """
    Calculates a match score using an 80% accuracy heuristic.
    Weights: Amount (45%), Description (40%), Polling Time Window (15%).
    Uses fuzzy matching for better description similarity.
    """
    score = 0.0

    # --- Weight 1: Amount Match (45%) ---
    AMOUNT_WEIGHT = 0.45
    AMOUNT_TOLERANCE = 1.50  # Allow $1.50 variance for potential fees

    if alert.get("amount") is not None and polled.get("amount") is not None:
        amount_diff = abs(alert["amount"] - polled["amount"])
        if amount_diff <= AMOUNT_TOLERANCE:
            score += AMOUNT_WEIGHT
        elif amount_diff < 5.00:
            score += AMOUNT_WEIGHT * 0.1

    # --- Weight 2: Description Match (40%) ---
    DESC_WEIGHT = 0.40
    if alert.get("description") and polled.get("description"):
        # Normalize to lowercase for fuzz ratio
        alert_desc = str(alert["description"]).lower().strip()
        polled_desc = str(polled["description"]).lower().strip()

        desc_similarity = fuzz.ratio(alert_desc, polled_desc) / 100.0
        score += desc_similarity * DESC_WEIGHT

    # --- Weight 3: Polling Time Window (15%) ---
    TIME_WEIGHT = 0.15
    try:
        alert_dt = datetime.strptime(alert["date"], '%Y-%m-%d').date() if alert.get("date") else datetime.now().date()
        polled_dt = polled["polled_at"].date()

        if alert_dt == polled_dt and (datetime.now() - polled["polled_at"]).total_seconds() < 24 * 3600:
            score += TIME_WEIGHT
    except Exception:
        pass

    return round(min(score, 1.0), 2)


# --- FASTAPI APPLICATION AND ENDPOINTS ---

app = FastAPI(
    title="A2A Telex Verification Agent",
    description="A simple, simulated AI agent for matching bank alert emails to a pre-polled transaction ledger."
)
#
@app.get("/.well-known/agent.json", response_model=Dict[str, Any], tags=["A2A Protocol"])
def get_agent_manifest():
    """
    Simulates the A2A Agent Card for agent discovery.
    This tells other agents what this agent can do.
    """
    return {
        "name": "TelexVerificationAgent",
        "description": "Matches unstructured bank alert emails to structured ledger transactions with 80% confidence.",
        "url": "http://localhost:8000/", # Placeholder URL
        "version": "1.0.0",
        "skills": [
            {
                "id": "verify_transaction_alert",
                "name": "Verify Bank Alert",
                "description": "Takes a bank alert email (string) and returns the matched transaction details from the ledger.",
                "tags": ["finance", "verification", "security"],
                "input_schema": {"type": "string", "name": "email_content"},
                "output_schema": AgentArtifact.model_json_schema()
            }
        ]
    }

@app.post("/process_alert", response_model=AgentArtifact, tags=["A2A Protocol"])
def process_alert(request: AlertRequest):
    """
    The main A2A Task endpoint. Receives the email content, runs the logic, and returns the Artifact.
    """
    email_content = request.email_content
    
    # 1. PERCEIVE: Parse the email content
    alert_data = parse_email_alert(email_content)
    
    if alert_data["amount"] is None or alert_data["description"] is None:
        raise HTTPException(status_code=400, detail="Agent failed to reliably parse amount or description from the email.")

    # 2. REASON: Find the best match in the ledger
    best_match: PolledTransaction | None = None
    highest_score: float = 0.0

    for tx_id, polled_tx_dict in TRANSACTION_LEDGER.items():
        polled_tx = PolledTransaction(**polled_tx_dict)
        score = calculate_match_score(alert_data, polled_tx_dict)
        
        if score > highest_score:
            highest_score = score
            best_match = polled_tx

    # 3. ACT: Return the final artifact based on the threshold
    if highest_score >= ACCURACY_THRESHOLD and best_match:
        # Update ledger status (simulating a tool call to a database)
        TRANSACTION_LEDGER[best_match.tx_id]["verified"] = True
        
        artifact = AgentArtifact(
            status="COMPLETED",
            match_found=True,
            match_score=highest_score,
            alert_data=alert_data,
            matched_transaction=best_match,
            message=f"SUCCESS: Alert matched transaction {best_match.tx_id} with {highest_score*100:.2f}% confidence."
        )
    else:
        artifact = AgentArtifact(
            status="COMPLETED",
            match_found=False,
            match_score=highest_score,
            alert_data=alert_data,
            matched_transaction=None,
            message=f"FAIL: No transaction met the {ACCURACY_THRESHOLD*100:.0f}% accuracy threshold. Highest score was {highest_score*100:.2f}%."
        )
        
    return artifact

@app.get("/ledger", response_model=List[PolledTransaction], tags=["Diagnostics"])
def get_ledger():
    """
    Returns the current state of the in-memory transaction ledger for diagnostic purposes.
    """
    return [PolledTransaction(**tx) for tx in TRANSACTION_LEDGER.values()]

@app.post("/ledger/re-poll", tags=["Diagnostics"])
def re_poll_ledger():
    """
    Forces a refresh of the mock transaction ledger.
    """
    generate_mock_ledger()
    return {"message": "Transaction ledger re-polled successfully with new mock data."}

async def ingest_email_payload(raw_email: dict, parsed: dict):
    """
    Called by email_reader after fetching and parsing an email.
    Stores the email, runs matching, and optionally sends notifications.
    """
    sess = get_session()
    email_id = f"eml-{uuid.uuid4().hex[:8]}"

    # store parsed + raw email
    alert = EmailAlert(
        id=email_id,
        received_at=datetime.utcnow(),
        raw_subject=raw_email.get("subject"),
        raw_from=raw_email.get("sender"),
        raw_body=raw_email.get("body"),
        parsed_amount=parsed.get("amount"),
        parsed_currency=parsed.get("currency"),
        parsed_account_masked=parsed.get("account_masked"),
        parsed_reference=parsed.get("reference"),
        parsed_merchant=parsed.get("merchant"),
    )
    sess.add(alert)
    sess.commit()

    # get recent transactions (last 24h)
    candidates = get_recent_transactions()

    # run matching
    match_result = choose_best({
        "amount": parsed.get("amount"),
        "merchant": parsed.get("merchant"),
        "reference": parsed.get("reference"),
        "received_at": datetime.utcnow(),
    }, candidates)

    # record match run
    run = MatchRun(
        id=f"run-{uuid.uuid4().hex[:8]}",
        email_id=email_id,
        chosen_tx_id=(match_result["best"]["tx"]["id"] if match_result["best"] else None),
        candidates=json.dumps(match_result["candidates"]),
        score=(match_result["best"]["score"] if match_result["best"] else None),
        status=match_result["status"],
        created_at=datetime.utcnow(),
        note="Automatic IMAP ingest",
    )
    sess.add(run)
    sess.commit()
    sess.close()

    print(f"[EMAIL INGESTED] {email_id} → {match_result['status']} ({match_result['best']['score'] if match_result['best'] else 'N/A'}%)")

@app.get("/mailtrap/fetch", tags=["Mailtrap"])
def fetch_mailtrap_alerts():
    """
    Fetches messages directly from Mailtrap API and processes them.
    """
    messages = fetch_mailtrap_messages()
    print(f"[MAILTRAP] Retrieved {len(messages)} messages.")
    return {"message_count": len(messages), "messages": messages}

if __name__ == "__main__":
    # Note: To run this, save the code as telex_agent_app.py and use:
    # uvicorn telex_agent_app:app --reload
    print("Agent is ready. Use /docs endpoint to interact with the API.")
    # The actual uvicorn run is typically handled externally in deployment,
    # but the structure is complete.


__all__ = ["app", "calculate_match_score"]
