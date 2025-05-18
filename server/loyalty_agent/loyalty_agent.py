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
from .mock_data.mock_data import get_mock_data
from .chat_history import ChatHistory

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
        
        print("LoyaltyAgent initialized with LangChain")
    
    def create_chat_session(self) -> str:
        """Create a new chat session and return its ID"""
        return self.chat_history.create_session()
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the chat history for a session"""
        return self.chat_history.get_history(session_id)
    
    def clear_chat_history(self, session_id: str) -> None:
        """Clear the chat history for a session"""
        self.chat_history.clear_history(session_id)
    
    def process_question(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a natural language question about loyalty program data
        
        Args:
            question: The natural language question to process
            session_id: Optional session ID for chat history
            
        Returns:
            A dictionary containing the query understanding, SQL query, results,
            insights, and recommendations
        """
        try:
            print(f"Processing question: {question}")
            
            # Step 1: Generate SQL from the question
            sql_query = self._generate_sql(question, session_id)
            print(f"Generated SQL: {sql_query}")
            
            # Step 2: Execute the SQL query
            start_time = time.time()
            query_results, count = self._execute_query(sql_query)
            query_time = time.time() - start_time
            print(f"Query executed, returned {len(query_results)} rows in {query_time:.2f} seconds")
            
            # Step 3: Generate insights from the results
            analysis = self._generate_insights(question, sql_query, query_results)
            print(f"Generated insights: {analysis.get('title', 'No title')}")
            
            # Step 4: Prepare the response
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
            
            # Step 5: Add to chat history if session_id is provided
            if session_id:
                self.chat_history.add_message(session_id, question, response)
            
            return response
            
        except Exception as e:
            print(f"Error in LoyaltyAgent: {str(e)}")
            
            # Return a fallback response
            response = {
                "queryUnderstanding": "There was an error understanding your question.",
                "sqlQuery": "",
                "databaseResults": {
                    "count": 0,
                    "time": 0
                },
                "title": "Error Processing Query",
                "data": [],
                "insights": [
                    {
                        "id": 1,
                        "text": f"Error: {str(e)}"
                    }
                ],
                "recommendations": [
                    {
                        "id": 1,
                        "title": "Try Again",
                        "description": "Please try rephrasing your question or ask something else.",
                        "type": "other"
                    }
                ]
            }
            
            # Add error response to chat history if session_id is provided
            if session_id:
                self.chat_history.add_message(session_id, question, response)
            
            return response
    
    def get_schema(self) -> Dict[str, Any]:
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
        
        Return only the names of relevant tables as a JSON array, e.g., ["customers", "points_transactions"]"""
        
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
    
    def _generate_sql(self, question: str, session_id: Optional[str] = None) -> str:
        """
        Generate SQL from a natural language question
        
        Args:
            question: The natural language question
            session_id: Optional session ID to include chat history context
            
        Returns:
            A SQL query string
        """
        try:
            # First determine which tables are relevant
            relevant_tables = self.determine_relevant_tables(question, self.schema.tables, session_id)
    
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
            1. Only use the tables and columns defined in the schema
            2. Always use proper SQL syntax for the Redshift data warehouse dialect
            3. Include appropriate JOINs when information from multiple tables is needed
            4. Use descriptive aliases for tables (e.g., c for customers, pt for points_transactions)
            5. Limit results to 100 rows unless specified otherwise
            6. Use simple ORDER BY and GROUP BY clauses when appropriate
            7. Format the SQL query nicely with line breaks and proper indentation
            8. Only return a valid SQL query and nothing else
            9. If the question references previous queries or results, use that context to generate a more accurate query
            
            User question: {question}
            
            SQL Query:"""
            
            # Generate SQL with the language model
            response = self.model.invoke([HumanMessage(content=prompt)])
            
            # Extract the SQL query from the response
            sql_query = response.content.strip()
            
            return sql_query
            
        except Exception as e:
            print(f"Error generating SQL: {str(e)}")
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    def _execute_query(self, sql_query: str) -> tuple[List[Dict[str, Any]], int]:
        """
        Execute a SQL query by sending it to the API
        
        Args:
            sql_query: The SQL query to execute
            
        Returns:
            Tuple of (results list, count)
        """
        try:
            # Get API configuration from environment variables
            base_url = os.environ.get("DATABASE_API_URL", "https://example.com")
            api_key = os.environ.get("DATABASE_API_KEY", "")
            timeout = int(os.environ.get("API_TIMEOUT", "30000")) / 1000  # Convert to seconds
            
            print(f"Sending query to: {base_url}/query")
            
            # Make the API request
            response = requests.get(
                f"{base_url}/query",
                params={"query": sql_query},
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Loyalty-Insights-Agent/1.0"
                },
                timeout=timeout
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response JSON
            data = response.json()
            
            return data.get("results", []), data.get("count", 0)
            
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            print("Using mock data instead")
            
            # Use mock data as fallback
            mock_data = get_mock_data(sql_query)
            return mock_data, len(mock_data)
    
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
            3. 2-3 actionable business recommendations based on these insights
            
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
            }}"""
            
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