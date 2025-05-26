from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import json

class ResponseValidatorTool:
    def __init__(self, model: ChatOpenAI):
        self.model = model

    async def validate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if the response answers the question"""
        print("\n--- Validating Response ---")
        try:
            question = state["question"]
            sql_query = state["sql_query"]
            results = state["data"]
            
            prompt = f"""You are a data validation expert. Your task is to validate if the SQL query results properly answer the user's question.
            
            User question: {question}
            
            SQL query that was executed: {sql_query}
            
            Query results: {json.dumps(results)}
            
            IMPORTANT BUSINESS RULES:
            - Each client can only access their own data and their own customers
            - All queries MUST be filtered by client_id
            - This is a multi-tenant system where each client's data is isolated
            
            Please validate if:
            1. The results directly answer the user's question
            2. The results are complete and not missing important information
            3. The query is properly structured to get the required data
            4. The query correctly filters by client_id (this is required)
            
            Return a JSON object with the following structure:
            {{
                "is_valid": true/false,
                "needs_retry": true/false,
                "error_message": "Description of any issues found",
                "error_type": "validation_error"
            }}
            
            If the results are valid, set is_valid to true and needs_retry to false.
            If the results are invalid but could be fixed with a retry, set is_valid to false and needs_retry to true.
            If the results are invalid and cannot be fixed with a retry, set both is_valid and needs_retry to false."""
            
            print("Analyzing response validity...")
            response = await self.model.ainvoke([HumanMessage(content=prompt)])
            
            try:
                # Clean the response content
                content = response.content.strip()
                # Remove any markdown code block formatting
                content = content.replace('```json', '').replace('```', '').strip()
                
                # Try to parse the cleaned content
                validation = json.loads(content)
                
                # Validate the required fields
                required_fields = ["is_valid", "needs_retry", "error_message", "error_type"]
                if not all(field in validation for field in required_fields):
                    raise ValueError("Missing required fields in validation response")
                
                if validation["is_valid"]:
                    print("✓ Response validation passed")
                    state["error"] = {
                    "is_valid": True,
                    "needs_retry": False,
                    "error_message": None,
                    "error_type": None
                    }
                else:
                    print(f"✗ Response validation failed: {validation['error_message']}")
                    state["error"] = validation
                
                return state
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"✗ Error parsing validation response: {str(e)}")
                state["error"] = {
                    "is_valid": False,
                    "needs_retry": False,
                    "error_message": "Failed to validate response",
                    "error_type": "validation_error"
                }
                return state
                
        except Exception as e:
            print(f"✗ Error in response validation: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "needs_retry": False,
                "error_message": str(e),
                "error_type": "validation_error"
            }
            return state 