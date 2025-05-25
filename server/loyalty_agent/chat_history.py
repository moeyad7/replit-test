from typing import Dict, List, Any
import time
import uuid

class ChatHistory:
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
    
    async def create_session(self) -> str:
        """Create a new chat session and return its ID"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        return session_id
    
    async def add_message(self, session_id: str, question: str, response: Dict[str, Any]) -> None:
        """Add a message to the chat history"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} does not exist")
        
        self.sessions[session_id].append({
            "timestamp": time.time(),
            "question": question,
            "response": response
        })
    
    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the chat history for a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} does not exist")
        return self.sessions[session_id]
    
    async def clear_history(self, session_id: str) -> None:
        """Clear the chat history for a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} does not exist")
        self.sessions[session_id] = [] 