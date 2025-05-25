from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import time
import os
import logging
import operator

from langchain_core.messages import HumanMessage
from .models.schema import DatabaseSchema
from .utils.schema_utils import load_database_schema
from .chat_history import ChatHistory
from .tools.sql_generator import SQLGeneratorTool
from .tools.insights_generator import InsightsGeneratorTool
from .tools.query_executor import QueryExecutorTool
from .tools.security_validator import SecurityValidatorTool
from .tools.response_validator import ResponseValidatorTool

# Configure logging
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for the loyalty agent workflow"""
    question: Annotated[str, operator.add]  # Using operator.add as reducer
    session_id: Annotated[Optional[str], lambda x, y: y]  # Keep the last value
    client_id: Annotated[int, lambda x, y: y]  # Keep the last value
    chat_context: Annotated[str, operator.add]  # Using operator.add as reducer
    schema: Annotated[List[Any], lambda x, y: y]  # Keep the last schema
    sql_query: Annotated[Optional[str], lambda x, y: y]  # Keep the last value
    data: Annotated[Optional[List[Dict[str, Any]]], lambda x, y: y]  # Keep the last value
    result_count: Annotated[Optional[int], lambda x, y: y]  # Keep the last value
    query_time: Annotated[Optional[float], lambda x, y: y]  # Keep the last value
    insights: Annotated[Optional[Dict[str, Any]], lambda x, y: {**x, **y} if x and y else y or x]  # Merge dictionaries if both exist
    error: Annotated[Optional[Dict[str, Any]], lambda x, y: y]  # Keep the last error
    retry_count: Annotated[int, operator.add]  # Sum retry counts

class LoyaltyAgent:
    """LoyaltyAgent processes natural language questions about loyalty program data using LangGraph"""
    
    def __init__(self):
        """Initialize the LoyaltyAgent with tools and graph"""
        print("\n=== Initializing LoyaltyAgent ===")
        
        # Get API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize the language model
        try:
            print("Initializing OpenAI model...")
            self.model = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=api_key
            )
            # Test the model with a simple prompt
            self.model.invoke([HumanMessage(content="test")])
            print("✓ OpenAI model initialized")
        except Exception as e:
            print(f"✗ Error initializing OpenAI model: {str(e)}")
            raise ValueError(f"Failed to initialize OpenAI model: {str(e)}")
        
        # Initialize chat history
        self.chat_history = ChatHistory()
        
        # Initialize tools
        try:
            print("Initializing tools...")
            self.sql_generator = SQLGeneratorTool(self.model)
            self.insights_generator = InsightsGeneratorTool(self.model)
            self.query_executor = QueryExecutorTool()
            self.security_validator = SecurityValidatorTool()
            self.response_validator = ResponseValidatorTool(self.model)
            print("✓ Tools initialized")
        except Exception as e:
            print(f"✗ Error initializing tools: {str(e)}")
            raise ValueError(f"Failed to initialize tools: {str(e)}")
        
        # Build the graph
        try:
            print("Building LangGraph workflow...")
            self.graph = self._build_graph()
            print("✓ LangGraph workflow built")
        except Exception as e:
            print(f"✗ Error building LangGraph workflow: {str(e)}")
            raise ValueError(f"Failed to build LangGraph workflow: {str(e)}")
        
        print("=== LoyaltyAgent initialized successfully ===\n")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Define the nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("execute_query", self._execute_query)
        workflow.add_node("validate_response", self._validate_response)
        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("create_error", self._create_error)
        
        # Define conditional edges
        def has_error(state: AgentState) -> bool:
            return state["error"] and not state["error"]["is_valid"]
        
        # Define the edges with conditions
        workflow.add_conditional_edges(
            "validate_input",
            lambda x: "create_error" if has_error(x) else "generate_sql"
        )
        workflow.add_conditional_edges(
            "generate_sql",
            lambda x: "create_error" if has_error(x) else "execute_query"
        )
        workflow.add_conditional_edges(
            "execute_query",
            lambda x: "create_error" if has_error(x) else "validate_response"
        )
        workflow.add_conditional_edges(
            "validate_response",
            lambda x: "create_error" if has_error(x) else "generate_insights"
        )
        
        # Add final edges
        workflow.add_edge("generate_insights", END)
        workflow.add_edge("create_error", END)
        
        # Set the entry point
        workflow.set_entry_point("validate_input")
        
        return workflow.compile()
    
    async def _validate_input(self, state: AgentState) -> AgentState:
        """Validate the input question"""
        print("\n--- Validating Input ---")
        state = await self.security_validator.validate_input(state)
        if not state["error"]["is_valid"]:
            print(f"✗ Input validation failed: {state['error']['error_message']}")
        else:
            print("✓ Input validation passed")
        return state
    
    async def _generate_sql(self, state: AgentState) -> AgentState:
        """Generate SQL from the question"""
        print("\n--- Generating SQL ---")
        try:
            
            # First determine relevant tables and update schema
            state = await self.sql_generator.determine_relevant_tables(state)
            
            # Then generate SQL using the filtered schema
            state = await self.sql_generator.generate_sql(state)
            
            # Validate SQL security
            state = await self.security_validator.validate_sql(state)
            if not state["error"]["is_valid"]:
                print(f"✗ SQL validation failed: {state['error']['error_message']}")
                return state
            
            print("✓ SQL generated and validated")
            return state
            
        except Exception as e:
            print(f"✗ Error generating SQL: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": str(e),
                "error_type": "sql_generation_error"
            }
            return state
    
    async def _execute_query(self, state: AgentState) -> AgentState:
        """Execute the SQL query"""
        print("\n--- Executing Query ---")
        try:
            start_time = time.time()
            state = await self.query_executor.execute_query(state)
            query_time = time.time() - start_time
            
            print(f"✓ Query executed in {query_time:.2f} seconds, returned {state['result_count']} rows")
            state["query_time"] = query_time
            return state
            
        except Exception as e:
            print(f"✗ Error executing query: {str(e)}")
            state["error"] = {
                "error_type": "query_execution_error",
                "error_message": str(e)
            }
            return state
    
    async def _validate_response(self, state: AgentState) -> AgentState:
        """Validate if the response answers the question"""
        print("\n--- Validating Response ---")
        validation = await self.response_validator.validate_response(state)
        
        if not validation["is_valid"]:
            if validation["needs_retry"] and state["retry_count"] < 3:
                print(f"! Response validation failed, retrying (attempt {state['retry_count'] + 1}/3)")
                state["retry_count"] += 1
                return state
            else:
                print(f"✗ Response validation failed: {validation['error_message']}")
                state["error"] = {
                    "error_type": validation["error_type"],
                    "error_message": validation["error_message"]
                }
                return state
        
        print("✓ Response validation passed")
        return state
    
    async def _generate_insights(self, state: AgentState) -> AgentState:
        """Generate insights from the query results"""
        print("\n--- Generating Insights ---")
        try:
            insights = await self.insights_generator.generate_insights(state)
            print("✓ Insights generated")
            state["insights"] = insights
            return state
            
        except Exception as e:
            print(f"✗ Error generating insights: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": str(e),
                "error_type": "insights_generation_error"
            }
            return state
    
    async def _create_error(self, state: AgentState) -> AgentState:
        """Create a standardized error response"""
        print("\n--- Creating Error Response ---")
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
            }
        }
        
        error_info = error_responses.get(
            state["error"]["error_type"],
            {
                "title": "Error",
                "message": state["error"]["error_message"],
                "type": "error"
            }
        )
        
        print(f"! Creating error response: {error_info['title']}")
        state["insights"] = {
            "title": error_info["title"],
            "insights": [{
                "id": 1,
                "text": error_info["message"]
            }],
            "recommendations": [{
                "id": 1,
                "title": "Try Again",
                "description": "Please rephrase your question or try different parameters.",
                "type": "other"
            }]
        }
        
        return state
    
    async def process_question(self, question: str, session_id: Optional[str] = None, client_id: int = 5252) -> Dict[str, Any]:
        """Process a natural language question about loyalty program data"""
        print(f"\n=== Processing Question ===")
        print(f"Question: {question}")
        if session_id:
            print(f"Session ID: {session_id}")
        print(f"Client ID: {client_id}")
        
        try:
            # Get chat history if session_id is provided
            chat_context = ""
            if session_id:
                try:
                    history = await self.chat_history.get_history(session_id)
                    if history:
                        chat_context = "\n\nPrevious conversation context:\n"
                        for msg in history[-3:]:  # Only include last 3 messages
                            chat_context += f"Q: {msg['question']}\n"
                            chat_context += f"A: {msg['response']['queryUnderstanding']}\n"
                            chat_context += f"SQL: {msg['response']['sqlQuery']}\n\n"
                except Exception as e:
                    print(f"! Warning: Could not get chat history: {str(e)}")
            
            # Create initial state
            state = AgentState(
                question=question,
                session_id=session_id,
                client_id=client_id,
                chat_context=chat_context,
                schema=[],  # Add schema to initial state
                sql_query=None,
                data=None,  # Renamed from query_results
                result_count=None,
                query_time=None,
                insights=None,
                error={
                    "is_valid": True,
                    "error_message": None,
                    "error_type": None
                },
                retry_count=0
            )
            
            # Run the graph
            print("\nStarting LangGraph workflow...")
            final_state = await self.graph.ainvoke(state)
            
            # Check if there was an error
            if final_state["error"] and not final_state["error"]["is_valid"]:
                error_type = final_state["error"]["error_type"]
                error_message = final_state["error"]["error_message"]
                
                # Create user-friendly error message based on error type
                user_message = self._get_user_friendly_error_message(error_type, error_message)
                
                return {
                    "queryUnderstanding": user_message,
                    "sqlQuery": final_state["sql_query"] or "",
                    "databaseResults": {
                        "count": final_state["result_count"] or 0,
                        "time": final_state["query_time"] or 0
                    },
                    "title": "Unable to Process Request",
                    "data": [],
                    "insights": [{
                        "id": 1,
                        "text": user_message
                    }],
                    "recommendations": [{
                        "id": 1,
                        "title": "Try Again",
                        "description": "Please rephrase your question or try different parameters.",
                        "type": "other"
                    }],
                    "error": {
                        "type": error_type,
                        "message": error_message
                    }
                }
            
            # Prepare response for successful case
            response = {
                "queryUnderstanding": f"I'm looking for loyalty program data that answers: '{question}'",
                "sqlQuery": final_state["sql_query"] or "",
                "databaseResults": {
                    "count": final_state["result_count"] or 0,
                    "time": final_state["query_time"] or 0
                },
                "title": final_state["insights"]["title"],
                "data": final_state["data"] or [],
                "insights": final_state["insights"]["insights"],
                "recommendations": final_state["insights"]["recommendations"]
            }
            
            # Add to chat history if session_id is provided
            if session_id:
                await self.chat_history.add_message(session_id, question, response)
            
            print("\n=== Question Processing Complete ===\n")
            return response
            
        except Exception as e:
            print(f"\n✗ Error in LoyaltyAgent: {str(e)}")
            return {
                "queryUnderstanding": "I encountered an error while processing your request.",
                "sqlQuery": "",
                "databaseResults": {
                    "count": 0,
                    "time": 0
                },
                "title": "System Error",
                "data": [],
                "insights": [{
                    "id": 1,
                    "text": "An unexpected error occurred. Please try again later."
                }],
                "recommendations": [{
                    "id": 1,
                    "title": "Try Again",
                    "description": "Please try your request again in a few moments.",
                    "type": "other"
                }],
                "error": {
                    "type": "system_error",
                    "message": str(e)
                }
            }
    
    def _get_user_friendly_error_message(self, error_type: str, error_message: str) -> str:
        """Convert technical error messages into user-friendly messages"""
        error_messages = {
            "security_violation": "Your question contains potentially harmful content. Please rephrase it.",
            "client_id_violation": "I cannot process questions that reference specific client IDs.",
            "missing_client_id": "I'm unable to process your request at this time. Please try again.",
            "dangerous_operation": "The requested operation is not allowed.",
            "max_retries_exceeded": "I'm having trouble understanding your question. Could you please rephrase it?",
            "sql_generation_error": "I'm having trouble converting your question into a database query. Please try rephrasing it.",
            "query_execution_error": "I encountered an error while retrieving the data. Please try again.",
            "validation_error": "I couldn't validate the results properly. Please try rephrasing your question.",
            "insights_generation_error": "I'm having trouble analyzing the data. Please try a different question."
        }
        
        return error_messages.get(error_type, "I encountered an error while processing your request. Please try again.")
    
    async def create_chat_session(self, client_id: int = 5252) -> str:
        """Create a new chat session and return its ID"""
        session_id = await self.chat_history.create_session()
        return session_id
    
    async def get_chat_history(self, session_id: str, client_id: int = 5252) -> List[Dict[str, Any]]:
        """Get the chat history for a session"""
        return await self.chat_history.get_history(session_id)
    
    async def clear_chat_history(self, session_id: str, client_id: int = 5252) -> None:
        """Clear the chat history for a session"""
        await self.chat_history.clear_history(session_id)
    
    async def get_schema(self, client_id: int = 5252) -> Dict[str, Any]:
        """Get the database schema information"""
        return await self.schema.to_dict() 