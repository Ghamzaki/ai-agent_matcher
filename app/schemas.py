from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransactionIn(BaseModel):
    id: Optional[str]
    timestamp: Optional[datetime]
    account_masked: Optional[str]
    merchant: Optional[str]
    amount: float
    currency: Optional[str] = "NGN"
    is_simulated: Optional[bool] = True

class EmailIn(BaseModel):
    id: Optional[str]
    received_at: Optional[datetime]
    subject: Optional[str]
    sender: Optional[str]
    body: str