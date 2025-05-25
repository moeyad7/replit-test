from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..utils.schema_utils import format_schema_for_prompt, get_table_name_description
import json

class SQLGeneratorTool:
    def __init__(self, model: ChatOpenAI):
        self.model = model

    async def determine_relevant_tables(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine which tables are relevant for the question"""
        print("\n--- Determining Relevant Tables ---")
        try:
            question = state["question"]
            
            # Get table descriptions
            table_descriptions = get_table_name_description()
            
            # Create a JSON-formatted description of available tables
            tables_json = json.dumps(table_descriptions, indent=2)
            
            prompt = f"""Given the user's question about a loyalty program database, identify which tables are needed to answer it.
            
            User question: {question}
            
            Available tables and their descriptions:
            {tables_json}
            
            Guidelines:
            1. Only select tables that are directly relevant to answering the question
            2. Consider the relationships between tables
            3. Include tables that contain necessary filtering or joining information
            4. Exclude tables that are not needed for the query
            
            IMPORTANT: You must respond with a valid JSON array of strings containing ONLY the table names.
            Example response format:
            ["table1", "table2"]
            
            Do not include any other text or explanation, just the JSON array."""
            
            print("Analyzing question to determine relevant tables...")
            response = await self.model.ainvoke([HumanMessage(content=prompt)])
            
            try:
                # Clean the response content
                content = response.content.strip()
                # Remove any markdown code block formatting
                content = content.replace('```json', '').replace('```', '').strip()
                
                # Parse the response as JSON
                relevant_tables = json.loads(content)
                if not isinstance(relevant_tables, list):
                    raise ValueError("Response is not a list")
                if not all(isinstance(table, str) for table in relevant_tables):
                    raise ValueError("Response contains non-string values")
                if not relevant_tables:
                    raise ValueError("Response is an empty list")
                
                # Store only the list of relevant table names in state
                state["schema"] = relevant_tables
                print(f"✓ Identified {len(relevant_tables)} relevant tables: {', '.join(relevant_tables)}")
                return state
                    
            except Exception as parse_error:
                print(f"✗ Error parsing tables JSON: {str(parse_error)}")
                print(f"Raw response: {response.content}")
                state["error"] = {
                    "is_valid": False,
                    "error_message": f"Failed to determine relevant tables: {str(parse_error)}",
                    "error_type": "table_selection_error"
                }
                return state
                
        except Exception as e:
            print(f"✗ Error determining relevant tables: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": str(e),
                "error_type": "table_selection_error"
            }
            return state

    async def generate_sql(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query from natural language question"""
        print("\n--- Generating SQL Query ---")
        try:
            question = state["question"]
            relevant_tables = state["schema"]  # This is now a list of table names
            client_id = state["client_id"]
            
            # Format schema for prompt
            schema_prompt = format_schema_for_prompt(relevant_tables)
            
            prompt = f"""You are a SQL expert. Your task is to convert a natural language question into a SQL query.
            
            User question: {question}
            
            Relevant database schema:
            {schema_prompt}
            
            Important guidelines:
            1. ALWAYS filter by client_id = {client_id}
            2. Use proper SQL syntax and formatting
            3. Include only necessary columns
            4. Use appropriate JOINs if multiple tables are needed
            5. Add ORDER BY if the question implies any sorting
            6. Use LIMIT if the question implies any limit
            7. Use appropriate aggregation functions (COUNT, SUM, AVG, etc.) if needed
            8. Format the output as a single, properly formatted SQL query
            
            Return ONLY the SQL query, nothing else."""
            
            print("Generating SQL query...")
            response = await self.model.ainvoke([HumanMessage(content=prompt)])
            
            # Clean and validate the response
            sql_query = response.content.strip()
            
            # Remove any markdown code block formatting
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            
            if not sql_query:
                raise ValueError("Empty SQL query generated")
                
            print("✓ SQL query generated successfully")
            print(sql_query)
            state["sql_query"] = sql_query
            return state
            
        except Exception as e:
            print(f"✗ Error generating SQL query: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": str(e),
                "error_type": "sql_generation_error"
            }
            return state