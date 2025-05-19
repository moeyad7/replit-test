import re
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

class SecurityValidator:
    def __init__(self):
        # Patterns to check for SQL injection and security violations
        self.dangerous_patterns = [
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'TRUNCATE\s+TABLE',
            r'ALTER\s+TABLE',
            r'UPDATE\s+.*\s+SET',
            r'INSERT\s+INTO',
            r'CREATE\s+TABLE',
            r';\s*--',  # SQL injection attempts
            r'UNION\s+ALL',
            r'EXEC\s+',
            r'EXECUTE\s+',
            r'xp_cmdshell',
            r'client_id\s*=\s*\d+',  # Attempt to override client_id
            r'client_id\s*!=\s*\d+',  # Attempt to exclude client_id
        ]
        
        # Additional dangerous commands to check in input questions
        self.dangerous_commands = [
            'drop',
            'delete',
            'truncate',
            'alter',
            'update',
            'insert',
            'create',
            'exec',
            'execute',
            'union'
        ]
        
        # Patterns to detect ID specifications in questions
        self.id_patterns = [
            # Client ID patterns
            r'client\s+id\s+\d+',
            r'client_id\s+\d+',
            r'clientid\s+\d+',
            r'client\s+=\s+\d+',
            r'client_id\s*=\s*\d+',
            r'client\s+number\s+\d+',
            r'client\s+#\s*\d+',
            # Generic ID patterns
            r'\bid\s+\d+\b',
            r'\bid\s*=\s*\d+\b',
            r'\bid\s*:\s*\d+\b',
            r'\bid\s*#\s*\d+\b',
            r'\bid\s+number\s+\d+\b',
            r'\bid\s+is\s+\d+\b',
            r'\bid\s+of\s+\d+\b',
            # Number patterns that might be IDs
            r'\bnumber\s+\d+\b',
            r'\b#\s*\d+\b',
            r'\b=\s*\d+\b',
            r'\b:\s*\d+\b'
        ]
        
    def validate_input(self, question: str) -> dict:
        """
        Validates the user's input question for security concerns
        """
        # Check for ID specifications in the question
        for pattern in self.id_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                return {
                    "is_valid": False,
                    "error_message": "ID specifications are not allowed in questions",
                    "error_type": "id_violation"
                }
        
        # Check for dangerous commands in the question
        question_lower = question.lower()
        for cmd in self.dangerous_commands:
            if cmd in question_lower:
                return {
                    "is_valid": False,
                    "error_message": f"Dangerous command '{cmd}' detected in question",
                    "error_type": "security_violation"
                }
        
        # Check for SQL injection patterns in the question
        for pattern in self.dangerous_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                return {
                    "is_valid": False,
                    "error_message": "Invalid input detected",
                    "error_type": "security_violation"
                }
            
        return {"is_valid": True, "error_message": "", "error_type": ""}
        
    def validate_sql(self, sql: str, client_id: int) -> dict:
        """
        Validates the generated SQL query for security concerns
        """
        # Ensure client_id filter is present (with or without quotes)
        client_id_pattern = f"client_id\\s*=\\s*['\"]?{client_id}['\"]?"
        if not re.search(client_id_pattern, sql, re.IGNORECASE):
            return {
                "is_valid": False,
                "error_message": "Missing client ID filter",
                "error_type": "missing_client_id"
            }
            
        # Check for dangerous operations
        for pattern in self.dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return {
                    "is_valid": False,
                    "error_message": "Dangerous SQL operation detected",
                    "error_type": "dangerous_operation"
                }
                
        return {"is_valid": True, "error_message": "", "error_type": ""}

class ResponseValidator:
    def __init__(self, model: ChatOpenAI):
        self.model = model
        print("ResponseValidator initialized with model")
        
    def validate_response(self, question: str, sql: str, response: dict) -> dict:
        """
        Validates if the response properly answers the question
        """
        
        # Handle different response types
        if isinstance(response, list):
            print(f"Response is a list with {len(response)} items")
            response_data = response
        elif isinstance(response, dict):
            print("Response is a dictionary")
            response_data = [response]
                    
        prompt = f"""
        Evaluate if this response properly answers the question.
        
        Original Question: {question}
        Generated SQL: {sql}
        Response: {json.dumps(response_data)}
        
        Check for:
        1. Does the SQL query match the question's intent?
        2. Are the results relevant to the question?
        3. Is there any missing information?
        4. Are there any SQL syntax issues?
        5. Are the results empty when they shouldn't be?
        
        Return a JSON with:
        {{
            "is_valid": boolean,
            "needs_retry": boolean,
            "error_message": string,
            "error_type": string,
            "confidence": float between 0 and 1
        }}
        """
        
        try:
            print("Sending validation request to model...")
            model_response = self.model.invoke([HumanMessage(content=prompt)])
            print(f"Raw model response: {model_response.content}")
            
            # Try to parse the model's response as JSON
            try:
                # Extract JSON from the response if it's wrapped in markdown code blocks
                json_str = model_response.content
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                
                validation_result = json.loads(json_str)
                print(f"Parsed validation result: {json.dumps(validation_result, indent=2)}")
                return validation_result
                
            except json.JSONDecodeError:
                # If JSON parsing fails, check for error indicators in the raw text
                if any(error_term in model_response.content.lower() for error_term in ["error:", "invalid:", "failed:", "cannot", "unable"]):
                    return {
                        "is_valid": False,
                        "needs_retry": True,
                        "error_message": "Response validation failed",
                        "error_type": "validation_error",
                        "confidence": 0.0
                    }
                # If no error indicators found, assume valid
                return {
                    "is_valid": True,
                    "needs_retry": False,
                    "error_message": "",
                    "error_type": "",
                    "confidence": 1.0
                }
            
        except Exception as e:
            print(f"Error during validation: {str(e)}")
            print("=== Response Validation Failed ===\n")
            return {
                "is_valid": False,
                "needs_retry": True,
                "error_message": f"Error validating response: {str(e)}",
                "error_type": "validation_error",
                "confidence": 0.0
            } 