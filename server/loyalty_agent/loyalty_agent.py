import os
import json
import time
from typing import Dict, List, Any, Optional, Union

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import requests

from .models.schema import Table, DatabaseSchema
from .utils.schema_utils import load_database_schema, format_schema_for_prompt
from .chat_history import ChatHistory
from .utils.validators import SecurityValidator, ResponseValidator

# Load environment variables
load_dotenv(override=True)  # Force override of existing variables
print("Environment variables loaded")
print("Current working directory:", os.getcwd())

class LoyaltyAgent:
    """
    LoyaltyAgent processes natural language questions about loyalty program data
    using LangChain and OpenAI to generate SQL and insights
    """
    
    def __init__(self):
        """Initialize the LoyaltyAgent with language models and database schema"""
        # Initialize the language model
        self.model = ChatOpenAI(
            model="gpt-4o-mini",  
            temperature=0,   # Deterministic outputs
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        
        # Load database schema
        self.schema = load_database_schema()
        
        # Initialize chat history
        self.chat_history = ChatHistory()
        
        # Initialize validators
        self.security_validator = SecurityValidator()
        self.response_validator = ResponseValidator(self.model)
        
        print("LoyaltyAgent initialized with LangChain")
    
    def create_chat_session(self, client_id: int = 5252) -> str:
        """Create a new chat session and return its ID"""
        return self.chat_history.create_session()
    
    def get_chat_history(self, session_id: str, client_id: int = 5252) -> List[Dict[str, Any]]:
        """Get the chat history for a session"""
        return self.chat_history.get_history(session_id)
    
    def clear_chat_history(self, session_id: str, client_id: int = 5252) -> None:
        """Clear the chat history for a session"""
        self.chat_history.clear_history(session_id)
    
    def process_question(self, question: str, session_id: Optional[str] = None, client_id: int = 5252) -> Dict[str, Any]:
        """
        Process a natural language question about loyalty program data
        
        Args:
            question: The natural language question to process
            session_id: Optional session ID for chat history
            client_id: The client ID to filter data for (default: 5252)
            
        Returns:
            A dictionary containing the query understanding, SQL query, results,
            insights, and recommendations
        """
        try:
            print("\n=== Starting Question Processing ===")
            print(f"Question: {question}")
            print(f"Session ID: {session_id}")
            print(f"Client ID: {client_id}")
            
            # Step 1: Security validation of input
            print("\n--- Step 1: Input Security Validation ---")
            security_check = self.security_validator.validate_input(question)
            print(f"Security check result: {json.dumps(security_check, indent=2)}")
            
            if not security_check["is_valid"]:
                print("Security validation failed, returning error response")
                return self._create_error_response(
                    security_check["error_message"],
                    security_check["error_type"]
                )
            
            # Step 2: Generate SQL with retry logic
            print("\n--- Step 2: SQL Generation and Validation ---")
            max_retries = 3
            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} of {max_retries}")
                try:
                    # Generate SQL
                    print("Generating SQL...")
                    sql_query = self._generate_sql(question, session_id, client_id)
                    print(f"Generated SQL: {sql_query}")
                    
                    # Validate SQL security
                    print("Validating SQL security...")
                    sql_check = self.security_validator.validate_sql(sql_query, client_id)
                    print(f"SQL security check result: {json.dumps(sql_check, indent=2)}")
                    
                    if not sql_check["is_valid"]:
                        if attempt == max_retries - 1:
                            print("SQL validation failed on final attempt")
                            return self._create_error_response(
                                sql_check["error_message"],
                                sql_check["error_type"]
                            )
                        print("SQL validation failed, retrying...")
                        continue
                    
                    # Execute query
                    print("\n--- Step 3: Query Execution ---")
                    start_time = time.time()
                    print("Executing query...")
                    query_results, count = self._execute_query(sql_query)
                    query_time = time.time() - start_time
                    print(f"Query executed in {query_time:.2f} seconds")
                    print(f"Returned {len(query_results)} rows")
                    
                    # Validate response
                    print("\n--- Step 4: Response Validation ---")
                    validation = self.response_validator.validate_response(
                        question, sql_query, query_results
                    )
                    
                    if validation["is_valid"]:
                        print("\n--- Step 5: Generating Insights ---")
                        # Generate insights
                        analysis = self._generate_insights(question, sql_query, query_results)
                        print(f"Generated insights: {analysis.get('title', 'No title')}")
                        
                        # Prepare response
                        print("\n--- Step 6: Preparing Final Response ---")
                        response = {
                            "queryUnderstanding": f"I'm looking for loyalty program data that answers: '{question}'",
                            "sqlQuery": sql_query,
                            "databaseResults": {
                                "count": count,
                                "time": query_time
                            },
                            "title": analysis.get("title", "Data Analysis"),
                            "data": query_results,
                            "insights": analysis.get("insights", []),
                            "recommendations": analysis.get("recommendations", [])
                        }
                        
                        # Add to chat history if session_id is provided
                        if session_id:
                            print("Adding response to chat history...")
                            self.chat_history.add_message(session_id, question, response)
                        
                        print("=== Question Processing Complete ===\n")
                        return response
                    
                    if not validation["needs_retry"]:
                        print("Response validation failed, no retry needed")
                        return self._create_error_response(
                            validation["error_message"],
                            validation["error_type"]
                        )
                    
                    print("Response validation failed, retrying...")
                    
                except Exception as e:
                    print(f"Error during attempt {attempt + 1}: {str(e)}")
                    if attempt == max_retries - 1:
                        print("Max retries exceeded")
                        return self._create_error_response(
                            "Please rephrase your question",
                            "max_retries_exceeded"
                        )
            
            print("All retry attempts failed")
            return self._create_error_response(
                "Unable to generate a valid response",
                "max_retries_exceeded"
            )
            
        except Exception as e:
            print(f"Error in LoyaltyAgent: {str(e)}")
            return self._create_error_response(
                f"Error processing question: {str(e)}",
                "processing_error"
            )
    
    def get_schema(self, client_id: int = 5252) -> Dict[str, Any]:
        """Get the database schema information"""
        return self.schema.to_dict()
    
    def determine_relevant_tables(self, question: str, all_tables: List[Table], session_id: Optional[str] = None) -> List[Table]:
        """
        Determine which tables are relevant to the user's question
        
        Args:
            question: The natural language question
            all_tables: List of all available tables
            session_id: Optional session ID to include chat history context
            
        Returns:
            List of relevant tables
        """
        # Create a simple prompt to identify relevant tables
        table_names = [table.name for table in all_tables]
        table_descriptions = {table.name: table.description for table in all_tables}
        
        # Get chat history if session_id is provided
        chat_context = ""
        if session_id:
            try:
                history = self.chat_history.get_history(session_id)
                if history:
                    chat_context = "\n\nPrevious conversation context:\n"
                    for msg in history[-3:]:  # Only include last 3 messages for context
                        chat_context += f"Q: {msg['question']}\n"
                        chat_context += f"SQL: {msg['response']['sqlQuery']}\n\n"
            except Exception as e:
                print(f"Warning: Could not get chat history: {str(e)}")
        
        prompt = f"""Given the user's question about a loyalty program database, identify which tables are needed to answer it.
        
        Available tables:
        {json.dumps(table_descriptions, indent=2)}
        
        {chat_context}
        
        Important guidelines:
        1. Consider the full context of the conversation when determining relevant tables
        2. If the question references previous queries (e.g., "their", "those", "same"), use the context to understand which tables are needed
        3. Include all tables that might be needed for the query, even if they're only referenced indirectly
        4. Be thorough in table selection to ensure all necessary data can be accessed
        
        User question: {question}
        
        Return only the names of relevant tables as a JSON array"""
        
        # Use a smaller model for this task to save tokens
        model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        response = model.invoke([HumanMessage(content=prompt)])    
        
        try:
            # Extract table names from response
            relevant_table_names = json.loads(response.content)
            return [table for table in all_tables if table.name in relevant_table_names]
        except:
            # Fallback to a simple keyword matching if parsing fails
            return [table for table in all_tables 
                    if table.name in question.lower() or 
                    any(word in question.lower() for word in table.name.split('_'))]
    
    def _generate_sql(self, question: str, session_id: Optional[str] = None, client_id: int = 5252) -> str:
        """
        Generate SQL from a natural language question
        
        Args:
            question: The natural language question
            session_id: Optional session ID to include chat history context
            client_id: The client ID to filter data for
            
        Returns:
            A SQL query string
        """
        try:
            # First determine which tables are relevant
            relevant_tables = self.determine_relevant_tables(question, self.schema.tables, session_id)
            if not relevant_tables:
                raise ValueError("No relevant tables found for the question")
    
            # Format only the relevant schema for the prompt
            schema_string = format_schema_for_prompt(relevant_tables)
            
            # Get chat history if session_id is provided
            chat_context = ""
            if session_id:
                try:
                    history = self.chat_history.get_history(session_id)
                    if history:
                        chat_context = "\n\nPrevious conversation context:\n"
                        for msg in history[-3:]:  # Only include last 3 messages for context
                            chat_context += f"Q: {msg['question']}\n"
                            chat_context += f"A: {msg['response']['queryUnderstanding']}\n"
                            chat_context += f"SQL: {msg['response']['sqlQuery']}\n\n"
                except Exception as e:
                    print(f"Warning: Could not get chat history: {str(e)}")
            
            # Create prompt for SQL generation
            prompt = f"""You are a SQL expert for a loyalty program database. Your task is to convert natural language questions 
            into SQL queries that can answer the question.
            
            Use the following database schema:
            {schema_string}
            
            {chat_context}
            
            Important guidelines:
            1. Always filter results by client_id = {client_id}
            2. Only use the tables and columns defined in the schema
            3. Always use proper SQL syntax for the Redshift data warehouse dialect
            4. Include appropriate JOINs when information from multiple tables is needed
            5. Use descriptive aliases for tables (e.g., c for customers, pt for points_transactions)
            6. Limit results to 100 rows unless specified otherwise
            7. Use simple ORDER BY and GROUP BY clauses when appropriate
            8. Format the SQL query nicely with line breaks and proper indentation
            9. Only return a valid SQL query and nothing else
            10. If the question references previous queries or results, use that context to generate a more accurate query
            
            User question: {question}
            
            Return only the SQL query as a string."""
            
            # Generate SQL using the language model
            response = self.model.invoke([HumanMessage(content=prompt)])
            sql_query = response.content.strip()
            
            return sql_query
            
        except Exception as e:
            print(f"Error generating SQL: {str(e)}")
            raise
    
    def _execute_query(self, sql_query: str) -> tuple[List[Dict[str, Any]], int]:
        """
        Execute a SQL query by sending it to the mock API
        
        Args:
            sql_query: The SQL query to execute
            
        Returns:
            Tuple of (results list, count)
        """
        try:
            # Use the local mock API
            base_url = "http://localhost:4000"
            
            print(f"Sending query to: {base_url}/query")
            
            # Make the API request
            response = requests.get(
                f"{base_url}/query",
                params={"query": sql_query},
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Loyalty-Insights-Agent/1.0"
                },
                timeout=30  # 30 second timeout
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response JSON
            data = response.json()
            
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
                
            print(results)
            
            return results, len(results)
            
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            # Return empty results on error
            return [], 0
    
    def _generate_insights(self, question: str, sql_query: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate insights from query results
        
        Args:
            question: The original question
            sql_query: The SQL query used
            data: The query results
            
        Returns:
            Dictionary containing title, insights, and recommendations
        """
        try:
            # Create prompt for insights generation
            prompt = f"""You are a business intelligence analyst for a loyalty program. Your task is to analyze the data from a SQL query and provide 
            valuable insights and recommendations.
            
            Original question: {question}
            
            SQL query that was executed: {sql_query}
            
            Query results: {json.dumps(data)}
            
            Please provide:
            1. A suitable title for this data analysis (keep it short and informative)
            2. 3-5 key insights from the data (focus on patterns, trends, or notable observations)
            3. 0-3 actionable business recommendations based on these insights (only include recommendations if they are truly valuable and actionable)
            
            Important guidelines:
            - Never reference internal client IDs in the insights or recommendations
            - Frame recommendations from the client's perspective (e.g., "Send targeted emails to your customers" instead of "Send emails to client 5252")
            - Only include recommendations if they are truly valuable and actionable
            - Focus on customer-centric insights and recommendations
            - Use "your customers" or "your loyalty program" instead of referencing specific client IDs
            
            Format your response as a JSON object with the following structure:
            {{
              "title": "Analysis title",
              "insights": [
                {{"id": 1, "text": "First insight..."}},
                {{"id": 2, "text": "Second insight..."}}
              ],
              "recommendations": [
                {{"id": 1, "title": "Recommendation title", "description": "Details...", "type": "email|award|other"}},
                {{"id": 2, "title": "Recommendation title", "description": "Details...", "type": "email|award|other"}}
              ]
            }}
            
            Note: The recommendations array can be empty if no actionable recommendations are warranted."""
            
            # Generate insights with the language model
            response = self.model.invoke([HumanMessage(content=prompt)])
            
            # Extract and parse the JSON from the response
            try:
                response_text = response.content.strip()
                # Find JSON in the response (in case it contains additional text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    analysis = json.loads(json_str)
                    return analysis
                else:
                    raise ValueError("No valid JSON found in response")
                    
            except Exception as parse_error:
                print(f"Error parsing insights JSON: {str(parse_error)}")
                
                # Fallback insights
                return {
                    "title": "Data Analysis",
                    "insights": [{"id": 1, "text": "Unable to parse insights from the analysis."}],
                    "recommendations": [{
                        "id": 1,
                        "title": "Retry Query",
                        "description": "Please try rephrasing your question for better results.",
                        "type": "other"
                    }]
                }
                
        except Exception as e:
            print(f"Error generating insights: {str(e)}")
            
            # Fallback insights
            return {
                "title": "Data Analysis",
                "insights": [{"id": 1, "text": "Unable to generate insights from the data."}],
                "recommendations": [{
                    "id": 1,
                    "title": "Review Query",
                    "description": "The current query may not be providing enough data for meaningful analysis.",
                    "type": "other"
                }]
            }
    
    def _create_error_response(self, message: str, error_type: str) -> dict:
        """
        Creates a standardized error response
        """
        error_responses = {
            "security_violation": {
                "title": "Security Check Failed",
                "message": "Your question contains potentially harmful content. Please rephrase.",
                "type": "error"
            },
            "client_id_violation": {
                "title": "Invalid Client ID",
                "message": "Client ID cannot be specified in the question.",
                "type": "error"
            },
            "missing_client_id": {
                "title": "System Error",
                "message": "Unable to process your request. Please try again.",
                "type": "error"
            },
            "dangerous_operation": {
                "title": "Invalid Operation",
                "message": "The requested operation is not allowed.",
                "type": "error"
            },
            "max_retries_exceeded": {
                "title": "Unable to Process",
                "message": "Please rephrase your question to be more specific.",
                "type": "error"
            },
            "processing_error": {
                "title": "Error",
                "message": message,
                "type": "error"
            }
        }
        
        error_info = error_responses.get(error_type, {
            "title": "Error",
            "message": message,
            "type": "error"
        })
        
        return {
            "queryUnderstanding": message,
            "sqlQuery": "",
            "databaseResults": {
                "count": 0,
                "time": 0
            },
            "title": error_info["title"],
            "data": [],
            "insights": [{
                "id": 1,
                "text": error_info["message"]
            }],
            "recommendations": [{
                "id": 1,
                "title": "Try Again",
                "description": "Please rephrase your question or try different parameters.",
                "type": "other"
            }],
            "error": {
                "type": error_type,
                "message": message
            }
        } 