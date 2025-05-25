from typing import List, Dict, Any, Tuple
import aiohttp
import time

class QueryExecutorTool:
    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url

    async def execute_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SQL query by sending it to the mock API"""
        print("\n--- Executing Query ---")
        try:
            sql_query = state["sql_query"]
            print(f"Sending query to: {self.base_url}/query")
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/query",
                    params={"query": sql_query},
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Loyalty-Insights-Agent/1.0"
                    },
                    timeout=30  # 30 second timeout
                ) as response:
                    # Check if request was successful
                    response.raise_for_status()
                    
                    # Parse response JSON
                    data = await response.json()
            
            # Handle the response data flexibly
            if isinstance(data, dict):
                # If the response is a single object, wrap it in a list
                results = [data]
            elif isinstance(data, list):
                # If the response is already a list, use it as is
                results = data
            else:
                # If the response is neither, wrap it in a dict and then a list
                results = [{"value": data}]
            
            print(f"✓ Query executed successfully, returned {len(results)} rows")
            
            # Update state with results
            state["data"] = results
            state["result_count"] = len(results)
            print(data)
            return state
            
        except Exception as e:
            print(f"✗ Error executing query: {str(e)}")
            # Update state with error
            state["error"] = {
                "is_valid": False,
                "error_message": str(e),
                "error_type": "query_execution_error"
            }
            state["data"] = []
            state["result_count"] = 0
            return state 