from typing import Dict, Any, List, Optional, TypedDict, Annotated

class AgentState(TypedDict):
    """State for the loyalty agent workflow"""
    # Core fields
    question: Annotated[str, lambda x, y: y]  # Keep the last value
    session_id: Annotated[Optional[str], lambda x, y: y]  # Keep the last value
    client_id: Annotated[int, lambda x, y: y]  # Keep the last value
    
    # Context and history
    chat_context: Annotated[Dict[str, Any], lambda x, y: {**x, **y} if x and y else y or x]  # Merge chat contexts
    
    # Current execution state
    current_sql_query: Annotated[Optional[str], lambda x, y: y]  # Current SQL query being executed
    current_data: Annotated[Optional[List[Dict[str, Any]]], lambda x, y: y]  # Current data from query
    
    # Error handling
    error: Annotated[Optional[Dict[str, Any]], lambda x, y: y]  # Keep the last error
    
    # Workflow control
    workflow_state: Annotated[Dict[str, Any], lambda x, y: {**x, **y} if x and y else y or x]  # Combined step and status
    response_type: Annotated[Dict[str, Any], lambda x, y: {**x, **y} if x and y else y or x]  # Combined decision and response

    @classmethod
    def create_initial_state(cls, question: str, session_id: Optional[str], client_id: int) -> 'AgentState':
        """Create initial state with default values"""
        return cls(
            question=question,
            session_id=session_id,
            client_id=client_id,
            chat_context={},
            current_sql_query=None,
            current_data=None,
            error={"is_valid": True, "error_message": None, "error_type": None},
            workflow_state={},
            response_type={}
        ) 