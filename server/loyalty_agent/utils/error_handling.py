from typing import Dict, Any

class ErrorMessages:
    """Centralized error messages for the loyalty agent"""
    
    # Error type to title mapping
    ERROR_TITLES = {
        "security_violation": "Security Check Failed",
        "client_id_violation": "Invalid Client ID",
        "missing_client_id": "System Error",
        "dangerous_operation": "Invalid Operation",
        "max_retries_exceeded": "Unable to Process",
        "validation_error": "Unable to Process",
        "sql_generation_error": "Query Generation Error",
        "query_execution_error": "Database Query Error",
        "insights_generation_error": "Analysis Error",
        "unexpected_error": "System Error",
        "unknown_error": "Unknown Error"
    }
    
    # User-friendly error messages
    USER_MESSAGES = {
        "security_violation": "Your question contains potentially harmful content. Please rephrase it.",
        "client_id_violation": "I cannot process questions that reference specific client IDs.",
        "missing_client_id": "I'm unable to process your request at this time. Please try again.",
        "dangerous_operation": "The requested operation is not allowed.",
        "validation_error": "I couldn't validate the results properly. Please try rephrasing your question.",
        "max_retries_exceeded": "I'm having trouble understanding your question. Could you please rephrase it?",
        "workflow_error": "I encountered an issue while processing your request. Please try again.",
        "sql_generation_error": "I'm having trouble converting your question into a database query. Please try rephrasing it.",
        "query_execution_error": "I encountered an error while retrieving the data. Please try again.",
        "table_selection_error": "I'm having trouble identifying the relevant data for your question. Please try rephrasing it.",
        "insights_generation_error": "I'm having trouble analyzing the data. Please try a different question.",
        "insights_parse_error": "I'm having trouble interpreting the analysis results. Please try again.",
        "unexpected_error": "An unexpected error occurred. Please try again later.",
        "unknown_error": "I encountered an error while processing your request. Please try again."
    }

def get_user_friendly_error_message(error_type: str, error_message: str) -> str:
    """Convert technical error messages into user-friendly messages"""
    # If we have a specific error message and it's not in our mapping, use it directly
    if error_type not in ErrorMessages.USER_MESSAGES and error_message:
        return error_message
        
    return ErrorMessages.USER_MESSAGES.get(error_type, "I'm having trouble processing your request. Please try rephrasing your question.")

def create_error_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Create an error response based on the error type"""
    # Get the original error message from the state
    error_message = state["error"]["error_message"]
    error_type = state["error"]["error_type"]
    
    error_title = ErrorMessages.ERROR_TITLES.get(error_type, "Error")
    
    # Clear all data and only keep error information
    state["sql_query"] = None
    state["data"] = None
    state["result_count"] = None
    state["query_time"] = None
    state["insights"] = {
        "title": error_title,
        "insights": [{
            "id": 1,
            "text": error_message
        }],
        "recommendations": [{
            "id": 1,
            "title": "Try Again",
            "description": "Please rephrase your question or try different parameters.",
            "type": "other"
        }]
    }
    state["step_status"] = "complete"
    return state 