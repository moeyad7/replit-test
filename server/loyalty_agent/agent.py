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
from .workflow_supervisor import WorkflowSupervisor, StepStatus

# Configure logging
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for the loyalty agent workflow"""
    question: Annotated[str, lambda x, y: y]  # Keep the last value
    session_id: Annotated[Optional[str], lambda x, y: y]  # Keep the last value
    client_id: Annotated[int, lambda x, y: y]  # Keep the last value
    chat_context: Annotated[Dict[str, Any], lambda x, y: {**x, **y} if x and y else y or x]  # Merge chat contexts
    schema: Annotated[List[Any], lambda x, y: y]  # Keep the last schema
    sql_query: Annotated[Optional[str], lambda x, y: y]  # Keep the last value
    data: Annotated[Optional[List[Dict[str, Any]]], lambda x, y: y]  # Keep the last value
    result_count: Annotated[Optional[int], lambda x, y: y]  # Keep the last value
    query_time: Annotated[Optional[float], lambda x, y: y]  # Keep the last value
    insights: Annotated[Optional[Dict[str, Any]], lambda x, y: {**x, **y} if x and y else y or x]  # Merge dictionaries if both exist
    error: Annotated[Optional[Dict[str, Any]], lambda x, y: y]  # Keep the last error
    retry_count: Annotated[int, operator.add]  # Sum retry counts
    next_step: Annotated[Optional[str], lambda x, y: y]  # Next step in workflow
    step_status: Annotated[Optional[StepStatus], lambda x, y: y]  # Status of current step

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
            self.security_validator = SecurityValidatorTool()
            self.sql_generator = SQLGeneratorTool(self.model, self.security_validator)
            self.insights_generator = InsightsGeneratorTool(self.model)
            self.query_executor = QueryExecutorTool()
            self.response_validator = ResponseValidatorTool(self.model)
            print("✓ Tools initialized")
        except Exception as e:
            print(f"✗ Error initializing tools: {str(e)}")
            raise ValueError(f"Failed to initialize tools: {str(e)}")
        
        # Initialize workflow supervisor
        self.supervisor = WorkflowSupervisor(max_retries=3)
        
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
        
        # Define the nodes with supervisor
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("execute_query", self._execute_query)
        workflow.add_node("validate_response", self._validate_response)
        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("create_error", self._create_error)
        
        # Define the routing function
        def route_next_step(state: AgentState) -> str:
            # If workflow is complete, end
            if self.supervisor.is_workflow_complete(state):
                return END
            
            # If we're in retry mode, respect the next_step
            if state.get("step_status") == StepStatus.RETRY:
                return state.get("next_step", END)
            
            # If there's an error, go to error handling
            if state.get("error") and not state["error"]["is_valid"]:
                return "create_error"
            
            # Use the next_step from supervisor
            return state.get("next_step", END)
        
        # Add conditional edges using the routing function
        workflow.add_conditional_edges(
            "validate_input",
            route_next_step
        )
        workflow.add_conditional_edges(
            "generate_sql",
            route_next_step
        )
        workflow.add_conditional_edges(
            "execute_query",
            route_next_step
        )
        workflow.add_conditional_edges(
            "validate_response",
            route_next_step
        )
        workflow.add_conditional_edges(
            "generate_insights",
            route_next_step
        )
        
        # Add final edges
        workflow.add_edge("create_error", END)
        
        # Set the entry point
        workflow.set_entry_point("validate_input")
        
        return workflow.compile()
    
    async def _validate_input(self, state: AgentState) -> AgentState:
        """Validate the input question"""
        return await self.supervisor.supervise_step(
            "validate_input",
            self.security_validator.validate_input,
            state,
            next_step="generate_sql",
            error_step="create_error"
        )
    
    async def _generate_sql(self, state: AgentState) -> AgentState:
        """Generate SQL from the question"""
        # Generate SQL using the consolidated function that includes validation
        state = await self.supervisor.supervise_step(
            "generate_sql",
            self.sql_generator.generate_sql,
            state,
            next_step="execute_query",
            error_step="create_error"
        )
        
        # If we're here, we have a valid SQL query
        # The execute_query step will handle retrying if needed
        return state
    
    async def _execute_query(self, state: AgentState) -> AgentState:
        """Execute the SQL query"""
        return await self.supervisor.supervise_step(
            "execute_query",
            self.query_executor.execute_query,
            state,
            next_step="validate_response",
            error_step="create_error"
        )
    
    async def _validate_response(self, state: AgentState) -> AgentState:
        """Validate if the response answers the question"""
        return await self.supervisor.supervise_step(
            "validate_response",
            self.response_validator.validate_response,
            state,
            next_step="generate_insights",
            error_step="create_error"
        )
    
    async def _generate_insights(self, state: AgentState) -> AgentState:
        """Generate insights from the results"""
        return await self.supervisor.supervise_step(
            "generate_insights",
            self.insights_generator.generate_insights,
            state,
            next_step=END,  # This is the final step
            error_step="create_error"
        )
    
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
            },
            "validation_error": {
                "title": "Unable to Process",
                "message": "I couldn't validate the results properly. Please try rephrasing your question.",
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
        
        # Clear all data and only keep error information
        state["sql_query"] = None
        state["data"] = None
        state["result_count"] = None
        state["query_time"] = None
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
            chat_context = {
                "previous_questions": [],
                "previous_sql_queries": [],
                "previous_insights": [],
                "current_step": "start",
                "workflow_history": []
            }
            
            if session_id:
                try:
                    history = await self.chat_history.get_history(session_id)
                    if history:
                        for msg in history[-3:]:  # Only include last 3 messages
                            chat_context["previous_questions"].append(msg["question"])
                            chat_context["previous_sql_queries"].append(msg["response"]["sqlQuery"])
                            if "insights" in msg["response"]:
                                chat_context["previous_insights"].append(msg["response"]["insights"])
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
                data=None,
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
            
            # Update chat context with final state
            final_state["chat_context"]["workflow_history"].append({
                "step": final_state["next_step"],
                "status": final_state["step_status"],
                "sql_query": final_state["sql_query"],
                "insights": final_state["insights"]
            })
            
            # Log the complete final state before response
            print("\n=== Complete Final State Before Response ===")
            print(f"Question: {final_state['question']}")
            print(f"Session ID: {final_state['session_id']}")
            print(f"Client ID: {final_state['client_id']}")
            print(f"Chat Context: {final_state['chat_context']}")
            print(f"Schema: {final_state['schema']}")
            print(f"SQL Query: {final_state['sql_query']}")
            print(f"Data: {final_state['data']}")
            print(f"Result Count: {final_state['result_count']}")
            print(f"Query Time: {final_state['query_time']}")
            print(f"Insights: {final_state['insights']}")
            print(f"Error: {final_state['error']}")
            print(f"Retry Count: {final_state['retry_count']}")
            print(f"Next Step: {final_state['next_step']}")
            print(f"Step Status: {final_state['step_status']}")
            print("==========================================\n")
            
            # Check if there was an error
            if final_state["error"] and not final_state["error"]["is_valid"]:
                error_type = final_state["error"]["error_type"]
                error_message = final_state["error"]["error_message"]
                
                # Create user-friendly error message based on error type
                user_message = self._get_user_friendly_error_message(error_type, error_message)
                
                response = {
                    "queryUnderstanding": user_message,
                    "sqlQuery": "",  # Empty string for SQL query on error
                    "databaseResults": {
                        "count": 0,
                        "time": 0
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
            else:
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