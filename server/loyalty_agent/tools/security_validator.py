from typing import Dict, Any
import re

class SecurityValidatorTool:
    def __init__(self):
        """Initialize the security validator with patterns for potentially harmful operations"""
        # Patterns for potentially harmful SQL operations
        self.dangerous_patterns = [
            r'\bDROP\b',
            r'\bDELETE\b',
            r'\bUPDATE\b',
            r'\bINSERT\b',
            r'\bTRUNCATE\b',
            r'\bALTER\b',
            r'\bEXEC\b',
            r'\bEXECUTE\b',
            r'\bUNION\b',
            r'\b--\b',  # SQL comments
            r'/\*.*?\*/',  # Multi-line SQL comments
            r';.*?;',  # Multiple statements
            r'@@',  # SQL Server variables
            r'0x[0-9a-fA-F]+',  # Hex values
            r'WAITFOR\s+DELAY',  # Time-based attacks
            r'BENCHMARK\s*\(',  # MySQL benchmark
            r'SLEEP\s*\(',  # Sleep function
            r'pg_sleep\s*\(',  # PostgreSQL sleep
        ]
        
        # Compile patterns for better performance
        self.pattern = re.compile('|'.join(self.dangerous_patterns), re.IGNORECASE)

    async def validate_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the input question for security"""
        print("\n--- Validating Input Security ---")
        try:
            question = state["question"]
            
            # Check for client_id in question
            if 'client_id' in question.lower():
                print("✗ Input contains client_id reference")
                state["error"] = {
                    "is_valid": False,
                    "error_message": "Client ID cannot be specified in the question",
                    "error_type": "client_id_violation"
                }
                return state
            
            # Check for dangerous patterns
            if self.pattern.search(question):
                print("✗ Input contains potentially harmful content")
                state["error"] = {
                    "is_valid": False,
                    "error_message": "Question contains potentially harmful content",
                    "error_type": "security_violation"
                }
                return state
            
            print("✓ Input security validation passed")
            state["error"] = {
                "is_valid": True,
                "error_message": None,
                "error_type": None
            }
            return state
            
        except Exception as e:
            print(f"✗ Error in input validation: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": str(e),
                "error_type": "validation_error"
            }
            return state

    async def validate_sql(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated SQL query for security"""
        print("\n--- Validating SQL Security ---")
        try:
            sql_query = state["sql_query"]
            client_id = state["client_id"]
            
            # Normalize the SQL query for comparison
            normalized_query = sql_query.lower().replace(" ", "")
            
            # Check for various client_id filter formats
            client_id_patterns = [
                f"client_id={client_id}",
                f"client_id='{client_id}'",
                f"client_id=\"{client_id}\"",
                f"client_id={client_id}",
                f"client_id='{client_id}'",
                f"client_id=\"{client_id}\""
            ]
            
            has_client_id = any(pattern in normalized_query for pattern in client_id_patterns)
            
            if not has_client_id:
                print(f"✗ SQL query missing client_id filter. Query: {sql_query}")
                state["error"] = {
                    "is_valid": False,
                    "error_message": "Query must filter by client_id",
                    "error_type": "missing_client_id"
                }
                return state
            
            # Check for dangerous patterns
            if self.pattern.search(sql_query):
                print("✗ SQL query contains potentially harmful operations")
                state["error"] = {
                    "is_valid": False,
                    "error_message": "Query contains potentially harmful operations",
                    "error_type": "dangerous_operation"
                }
                return state
            
            print("✓ SQL security validation passed")
            state["error"] = {
                "is_valid": True,
                "error_message": None,
                "error_type": None
            }
            return state
            
        except Exception as e:
            print(f"✗ Error in SQL validation: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": str(e),
                "error_type": "validation_error"
            }
            return state 