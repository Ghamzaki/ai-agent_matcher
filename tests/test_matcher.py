import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from datetime import datetime, timedelta
from app.main import calculate_match_score


def test_calculate_match_score_exact_match():
    alert = {
        "amount": 50.00,
        "description": "AMAZONPRCH",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    polled = {
        "amount": 50.00,
        "description": "AMAZONPRCH",
        "polled_at": datetime.now() - timedelta(hours=1),
    }
    score = calculate_match_score(alert, polled)
    assert 0.9 <= score <= 1.0  # should be a strong match


def test_calculate_match_score_partial_match():
    alert = {
        "amount": 51.00,  # slightly off
        "description": "AMAZONPRCH",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    polled = {
        "amount": 50.00,
        "description": "AMAZON",
        "polled_at": datetime.now(),
    }
    score = calculate_match_score(alert, polled)
    assert 0.90 <= score <= 0.98  # partial credit expected


def test_calculate_match_score_no_match():
    alert = {
        "amount": 500.00,
        "description": "UNKNOWNMERCHANT",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    polled = {
        "amount": 20.00,
        "description": "STARBUCKS",
        "polled_at": datetime.now(),
    }
    score = calculate_match_score(alert, polled)
    assert score < 0.3