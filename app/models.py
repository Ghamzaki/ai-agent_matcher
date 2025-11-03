from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Transaction(SQLModel, table=True):
    id: str = Field(primary_key=True)
    timestamp: datetime
    account_masked: Optional[str] = None
    merchant: Optional[str] = None
    amount: float
    currency: str = "NGN"
    extra_data: Optional[str] = None
    is_simulated: bool = True

class EmailAlert(SQLModel, table=True):
    id: str = Field(primary_key=True)
    received_at: datetime
    raw_subject: str
    raw_from: str
    raw_body: str
    parsed_amount: Optional[float] = None
    parsed_currency: Optional[str] = None
    parsed_account_masked: Optional[str] = None
    parsed_reference: Optional[str] = None
    parsed_merchant: Optional[str] = None

class MatchRun(SQLModel, table=True):
    id: str = Field(primary_key=True)
    email_id: str
    chosen_tx_id: Optional[str] = None
    candidates: Optional[str] = None
    score: Optional[float] = None
    status: str = "no_match"
    created_at: datetime
    note: Optional[str] = None