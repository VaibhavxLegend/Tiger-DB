"""
Mock graph data generators for realistic GraphRAG responses
Phase 2: Fast-track approach for hackathon

These generate realistic graph query responses without requiring full data load.
Can be swapped for real GSQL queries post-hackathon.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Realistic fraud patterns from closed_cases_history
FRAUD_PATTERNS = {
    "card_testing": {
        "typical_sequence": [2.50, 1.99, 0.50, 149.99],
        "time_window_minutes": 45,
        "device_new": True
    },
    "card_not_present_fraud": {
        "burst_count": 3,
        "time_window_hours": 24,
        "unusual_merchant": True
    },
    "out_of_region_use": {
        "new_region": True,
        "home_region_active": True
    }
}

# Sample devices from identity.csv patterns
SAMPLE_DEVICES = [
    {
        "id": "D000731",
        "type": "mobile",
        "info": "SAMSUNG SM-G935F Build/NRD90M",
        "os": "Android 7.0",
        "browser": "samsung browser 6.2",
        "screen": "2220x1080",
        "new_found": "New",
        "proxy_type": None
    },
    {
        "id": "D001523",
        "type": "desktop",
        "info": "Windows",
        "os": "Windows 10",
        "browser": "chrome 95.0",
        "screen": "1920x1080",
        "new_found": "Found",
        "proxy_type": "transparent"
    }
]

def generate_transaction_neighborhood(
    txn_id: str,
    card_id: str,
    customer_id: str,
    scenario: str = "suspicious"
) -> Dict[str, Any]:
    """
    Generate realistic transaction neighborhood data
    
    Args:
        txn_id: Transaction ID from case_pack
        card_id: Card ID from case_pack
        customer_id: Customer ID from case_pack
        scenario: "suspicious", "legitimate", or "uncertain"
    """
    
    # Parse IDs to get base numbers
    card_num = card_id.split('-')[0][1:]  # Extract number from C12345-K1
    
    # Generate transaction details
    base_amount = random.uniform(20, 500)
    
    transaction = {
        "transaction_id": txn_id,
        "amount": round(base_amount, 2),
        "timestamp": "2016-11-14 09:31:42",
        "channel": "online" if scenario != "legitimate" else random.choice(["online", "in_person"]),
        "product_cd": random.choice(["W", "C", "H"]),
        "risk_score": 0.79 if scenario == "suspicious" else (0.52 if scenario == "uncertain" else 0.23),
        "addr1": 444.0,
        "addr2": 87.0,
        "p_email_domain": "gmail.com"
    }
    
    # Card details
    card = {
        "card_id": card_id,
        "customer_id": customer_id,
        "network": random.choice(["visa", "mastercard", "american express"]),
        "type": random.choice(["credit", "debit"]),
        "issued_date": "2015-03-12"
    }
    
    # Customer history
    customer = {
        "customer_id": customer_id,
        "account_age_days": random.randint(200, 800),
        "total_transactions": random.randint(50, 300),
        "avg_transaction_amount": round(random.uniform(30, 150), 2),
        "fraud_history_count": 0 if scenario == "legitimate" else random.randint(0, 2)
    }
    
    # Recent transactions on same card
    recent_txns = []
    if scenario == "suspicious":
        # Card testing pattern
        for i, amt in enumerate([2.50, 1.99, 0.50]):
            recent_txns.append({
                "transaction_id": f"T{int(txn_id[1:]) - (3-i)}",
                "amount": amt,
                "timestamp": f"2016-11-14 0{8+i}:{45+i*3}:00",
                "channel": "online",
                "minutes_before_flagged": 40 - i*10
            })
    else:
        # Normal transactions
        for i in range(3):
            recent_txns.append({
                "transaction_id": f"T{int(txn_id[1:]) - (3-i)}",
                "amount": round(random.uniform(20, 100), 2),
                "timestamp": f"2016-11-{random.randint(1, 13)} {random.randint(10, 22)}:00:00",
                "channel": random.choice(["online", "in_person"]),
                "days_before_flagged": random.randint(1, 30)
            })
    
    # Device (if online)
    device = None
    if transaction["channel"] == "online":
        device = SAMPLE_DEVICES[0 if scenario == "suspicious" else 1].copy()
        device["times_seen_on_card"] = 1 if scenario == "suspicious" else 15
        device["first_seen_date"] = "2016-11-14" if scenario == "suspicious" else "2016-05-20"
    
    # Risk signals
    risk_signals = []
    if scenario == "suspicious":
        risk_signals = [
            "new_device_for_account",
            "multiple_small_transactions_before_large",
            "amount_above_card_average"
        ]
    elif scenario == "uncertain":
        risk_signals = [
            "higher_than_usual_amount",
            "new_merchant_category"
        ]
    
    return {
        "transaction": transaction,
        "card": card,
        "customer": customer,
        "device": device,
        "recent_transactions": recent_txns,
        "risk_signals": risk_signals,
        "query_metadata": {
            "hops": 2,
            "execution_time_ms": random.randint(50, 200),
            "vertices_examined": random.randint(100, 500)
        }
    }

def generate_shared_devices(
    card_id: str,
    scenario: str = "fraud_ring"
) -> Dict[str, Any]:
    """Generate shared device cluster data"""
    
    if scenario == "fraud_ring":
        # Multiple cards using same device
        device = SAMPLE_DEVICES[0].copy()
        
        shared_cards = [
            {
                "card_id": f"C00877-K1",
                "customer_id": "C00877",
                "first_used": "2016-11-12 14:23:11",
                "last_used": "2016-11-12 16:45:33",
                "transaction_count": 4,
                "total_amount": 287.65
            },
            {
                "card_id": card_id,
                "customer_id": card_id.split('-')[0],
                "first_used": "2016-11-14 09:12:00",
                "last_used": "2016-11-14 10:31:42",
                "transaction_count": 4,
                "total_amount": 264.42
            }
        ]
        
        return {
            "device": device,
            "shared_cards": shared_cards,
            "time_window_hours": 48,
            "pattern": "device_sharing_fraud_ring",
            "linked_closed_cases": ["CC-0141"],  # From closed_cases_history
            "risk_level": "high"
        }
    
    else:
        # Single card, no sharing
        return {
            "device": SAMPLE_DEVICES[1].copy(),
            "shared_cards": [{"card_id": card_id}],
            "time_window_hours": 720,
            "pattern": "normal_usage",
            "risk_level": "low"
        }

def generate_velocity_check(
    card_id: str,
    scenario: str = "testing"
) -> Dict[str, Any]:
    """Generate transaction velocity analysis"""
    
    if scenario == "testing":
        return {
            "card_id": card_id,
            "time_window_minutes": 40,
            "transaction_count": 4,
            "transactions": [
                {"amount": 2.50, "minutes_ago": 40},
                {"amount": 1.99, "minutes_ago": 25},
                {"amount": 0.50, "minutes_ago": 15},
                {"amount": 149.99, "minutes_ago": 0}
            ],
            "pattern_detected": "card_testing_sequence",
            "typical_velocity_for_card": 0.2,  # txns per hour normally
            "current_velocity": 6.0,  # txns per hour now
            "velocity_ratio": 30.0,
            "risk_level": "critical"
        }
    else:
        return {
            "card_id": card_id,
            "time_window_hours": 24,
            "transaction_count": 2,
            "transactions": [
                {"amount": 45.67, "hours_ago": 12},
                {"amount": 89.23, "hours_ago": 0}
            ],
            "pattern_detected": "normal",
            "typical_velocity_for_card": 2.5,
            "current_velocity": 2.0,
            "velocity_ratio": 0.8,
            "risk_level": "low"
        }

def generate_similar_past_cases(
    pattern: str,
    device_id: str = None,
    card_id: str = None
) -> List[Dict[str, Any]]:
    """Generate similar closed cases from history"""
    
    # Sample from closed_cases_history.csv patterns
    similar_cases = []
    
    if pattern == "card_testing" or device_id:
        similar_cases.append({
            "case_id": "CC-0141",
            "outcome": "confirmed_fraud",
            "pattern": "card_testing",
            "opened_at": "2016-08-15",
            "closed_at": "2016-08-15",
            "exposure_usd": 312.45,
            "n_txns": 5,
            "actions_taken": "BLOCK_CARD, CREATE_CASE, FILE_REPORT",
            "report_filed": True,
            "analyst_notes": "Textbook card testing: 3 sub-$5 authorizations followed by $298 purchase. Device matched current case.",
            "match_reason": "same_device_profile" if device_id else "same_pattern",
            "similarity_score": 0.92
        })
    
    if pattern == "card_not_present_fraud":
        similar_cases.append({
            "case_id": "CC-2671",
            "outcome": "confirmed_fraud",
            "pattern": "card_not_present_fraud",
            "opened_at": "2016-09-23",
            "closed_at": "2016-09-24",
            "exposure_usd": 445.67,
            "n_txns": 3,
            "actions_taken": "VERIFY_WITH_CUSTOMER, BLOCK_CARD, CREATE_CASE",
            "report_filed": False,
            "analyst_notes": "Customer denied transactions. Pattern: 3 online purchases in 18 hours, all different merchants.",
            "match_reason": "same_pattern",
            "similarity_score": 0.85
        })
    
    # Always include a cleared case for balance
    similar_cases.append({
        "case_id": "CC-3890",
        "outcome": "cleared",
        "pattern": "none",
        "opened_at": "2016-10-05",
        "closed_at": "2016-10-05",
        "exposure_usd": 0,
        "n_txns": 1,
        "actions_taken": "VERIFY_WITH_CUSTOMER, CLOSE_NO_FRAUD",
        "report_filed": False,
        "analyst_notes": "High risk score on legitimate purchase. Customer confirmed. New phone purchase triggered unusual pattern.",
        "match_reason": "similar_risk_score",
        "similarity_score": 0.45
    })
    
    return similar_cases

def generate_linked_cards(
    card_id: str,
    scenario: str = "normal"
) -> Dict[str, Any]:
    """Generate linked card analysis"""
    
    if scenario == "fraud_ring":
        return {
            "card_id": card_id,
            "linked_cards": [
                {
                    "card_id": "C00877-K1",
                    "link_type": "shared_device",
                    "link_strength": 0.95,
                    "first_linked_date": "2016-11-12",
                    "shared_attributes": ["device_D000731", "proxy_usage"]
                }
            ],
            "cluster_id": "CLUSTER_FR_0042",
            "cluster_size": 2,
            "risk_level": "high"
        }
    else:
        return {
            "card_id": card_id,
            "linked_cards": [],
            "cluster_id": None,
            "cluster_size": 1,
            "risk_level": "low"
        }
