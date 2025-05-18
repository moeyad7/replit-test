from typing import List, Dict, Any

def get_mock_customers() -> List[Dict[str, Any]]:
    """Get mock customer data"""
    return [
        {"id": 1, "first_name": "Michael", "last_name": "Scott", "email": "mscott@example.com", "points": 3542, "created_at": "2023-01-15"},
        {"id": 2, "first_name": "Jim", "last_name": "Halpert", "email": "jhalpert@example.com", "points": 2891, "created_at": "2023-01-20"},
        {"id": 3, "first_name": "Pam", "last_name": "Beesly", "email": "pbeesly@example.com", "points": 2745, "created_at": "2023-01-22"},
        {"id": 4, "first_name": "Dwight", "last_name": "Schrute", "email": "dschrute@example.com", "points": 2103, "created_at": "2023-02-01"},
        {"id": 5, "first_name": "Kelly", "last_name": "Kapoor", "email": "kkapoor@example.com", "points": 1986, "created_at": "2023-02-15"}
    ]

def get_mock_transactions() -> List[Dict[str, Any]]:
    """Get mock transaction data"""
    return [
        {"id": 1, "customer_id": 1, "points": 500, "transaction_date": "2023-05-01", "expiry_date": "2024-05-01", "source": "purchase", "description": "Online purchase"},
        {"id": 2, "customer_id": 1, "points": 200, "transaction_date": "2023-05-15", "expiry_date": "2024-05-15", "source": "referral", "description": "Friend referral"},
        {"id": 3, "customer_id": 2, "points": 350, "transaction_date": "2023-05-05", "expiry_date": "2024-05-05", "source": "purchase", "description": "In-store purchase"},
        {"id": 4, "customer_id": 3, "points": -150, "transaction_date": "2023-05-20", "expiry_date": None, "source": "redemption", "description": "Gift card redemption"},
        {"id": 5, "customer_id": 4, "points": 425, "transaction_date": "2023-05-10", "expiry_date": "2024-05-10", "source": "purchase", "description": "Mobile app purchase"}
    ]

def get_mock_challenges() -> List[Dict[str, Any]]:
    """Get mock challenge data"""
    return [
        {"id": 1, "name": "Summer Bonus", "description": "Make 3 purchases in June", "points": 500, "start_date": "2023-06-01", "end_date": "2023-06-30", "active": True},
        {"id": 2, "name": "Referral Drive", "description": "Refer a friend to join our program", "points": 300, "start_date": "2023-05-01", "end_date": "2023-07-31", "active": True},
        {"id": 3, "name": "Social Media", "description": "Share your purchase on social media", "points": 150, "start_date": "2023-04-15", "end_date": "2023-08-15", "active": True},
        {"id": 4, "name": "First Purchase", "description": "Complete your first purchase", "points": 200, "start_date": "2023-01-01", "end_date": "2023-12-31", "active": True},
        {"id": 5, "name": "Loyalty Anniversary", "description": "Celebrate your 1-year membership", "points": 500, "start_date": "2023-01-01", "end_date": "2023-12-31", "active": True}
    ]

def get_mock_challenge_completions() -> List[Dict[str, Any]]:
    """Get mock challenge completion data"""
    return [
        {"id": 1, "customer_id": 1, "challenge_id": 1, "completion_date": "2023-06-15", "points_awarded": 500},
        {"id": 2, "customer_id": 1, "challenge_id": 4, "completion_date": "2023-01-20", "points_awarded": 200},
        {"id": 3, "customer_id": 2, "challenge_id": 2, "completion_date": "2023-05-25", "points_awarded": 300},
        {"id": 4, "customer_id": 3, "challenge_id": 3, "completion_date": "2023-05-10", "points_awarded": 150},
        {"id": 5, "customer_id": 5, "challenge_id": 4, "completion_date": "2023-02-18", "points_awarded": 200}
    ]

def get_mock_data(sql_query: str) -> List[Dict[str, Any]]:
    """
    Get mock data based on the SQL query
    
    Args:
        sql_query: The SQL query string
        
    Returns:
        A list of mock data records
    """
    # Determine which mock data to return based on the query
    sql_lower = sql_query.lower()
    
    if "points_transactions" in sql_lower or "transaction" in sql_lower:
        return get_mock_transactions()
    elif "challenges" in sql_lower and "challenge_completions" not in sql_lower:
        return get_mock_challenges()
    elif "challenge_completions" in sql_lower or "completion" in sql_lower:
        return get_mock_challenge_completions()
    else:
        return get_mock_customers() 