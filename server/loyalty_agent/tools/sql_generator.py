from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..utils.schema_utils import format_schema_for_prompt, get_table_name_description
import json
import logging

from ..config.prompts import ToolPrompts
from .security_validator import SecurityValidatorTool

logger = logging.getLogger(__name__)

class SQLGeneratorTool:
    """Tool for generating SQL queries from natural language questions"""
    
    def __init__(self, model: ChatOpenAI, security_validator: SecurityValidatorTool):
        self.model = model
        self.security_validator = security_validator

    async def determine_relevant_tables(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine which tables are relevant for the question"""
        print("\n--- Determining Relevant Tables ---")
        try:
            question = state["question"]
            chat_context = state.get("chat_context", {})
            
            # Create prompt for determining relevant tables
            prompt = ToolPrompts.get_determine_relevant_tables_prompt(
                question=question,
                chat_context=chat_context
            )
            
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
                
                # Store the list of relevant table names in state
                state["schema"] = relevant_tables
                
                if not relevant_tables:
                    print("! No relevant tables identified for the question")
                    state["error"] = {
                        "is_valid": False,
                        "error_message": "Could not identify relevant tables for the question. The question may be unclear or require data not available in the database.",
                        "error_type": "no_relevant_tables"
                    }
                else:
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

    async def _generate_sql_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query from natural language question"""
        print("\n--- Generating SQL Query ---")
        try:
            question = state["question"]
            relevant_tables = state["schema"]  # This is now a list of table names
            client_id = state["client_id"]
            chat_context = state.get("chat_context", {})
            
            # Create prompt for SQL generation
            prompt = ToolPrompts.get_sql_generator_prompt(
                question=question,
                schema=relevant_tables,
                client_id=client_id,
                chat_context=chat_context
            )
            
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
            state["current_sql_query"] = sql_query
            return state
            
        except Exception as e:
            print(f"✗ Error generating SQL query: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": str(e),
                "error_type": "sql_generation_error"
            }
            return state

    async def generate_sql(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate the entire SQL generation process including validation"""
        # Step 1: Determine relevant tables
        state = await self.determine_relevant_tables(state)
        if state.get("error") and not state["error"]["is_valid"]:
            return state

        # Step 2: Generate SQL query
        state = await self._generate_sql_query(state)
        if state.get("error") and not state["error"]["is_valid"]:
            return state

        # Step 3: Validate SQL security
        state = await self.security_validator.validate_sql(state)
        if state.get("error") and not state["error"]["is_valid"]:
            return state

        return state