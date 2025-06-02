from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
import os
import logging
import json

from langchain_core.messages import HumanMessage, SystemMessage
from .chat_history import ChatHistory
from .tools.sql_generator import SQLGeneratorTool
from .tools.insights_generator import InsightsGeneratorTool
from .tools.query_executor import QueryExecutorTool
from .tools.security_validator import SecurityValidatorTool
from .workflow_supervisor import WorkflowSupervisor, TOOL_DESCRIPTIONS
from .models.state import AgentState
from .utils.error_handling import get_user_friendly_error_message
from .config.prompts import AgentPrompts

# Configure logging
logger = logging.getLogger(__name__)

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
            print("✓ Tools initialized")
        except Exception as e:
            print(f"✗ Error initializing tools: {str(e)}")
            raise ValueError(f"Failed to initialize tools: {str(e)}")
        
        # Initialize workflow supervisor
        self.supervisor = WorkflowSupervisor(max_retries=3)
        
        # Set up tools in the workflow supervisor
        self.supervisor.set_tools({
            tool_name: getattr(self, tool_name)
            for tool_name in TOOL_DESCRIPTIONS.keys()
        })
        
        print("=== LoyaltyAgent initialized successfully ===\n")
    
    async def _make_decision(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Decide whether to answer directly or use the workflow"""
        prompt = AgentPrompts.get_decision_prompt(state['question'], state['chat_context'])
        
        response = await self.model.ainvoke([HumanMessage(content=prompt)])
        try:
            decision = json.loads(response.content)
            state["decision"] = decision["decision"]
            return state
        except Exception as e:
            print(f"✗ Error parsing decision: {str(e)}")
            # Default to workflow if there's an error
            state["decision"] = "workflow"
            return state

    async def _generate_summary(self, state: Dict[str, Any], question: str) -> str:
        """Generate a summary response based on the current state and question"""
        try:
            if state["decision"] == "direct":
                prompt = AgentPrompts.get_direct_response_prompt(question, state['chat_context'])
            else:
                prompt = AgentPrompts.get_workflow_response_prompt(question, state)
            
            print("Generating summary response...")
            summary_response = await self.model.ainvoke([HumanMessage(content=prompt)])
            print("✓ Summary generated")
            return summary_response.content
            
        except Exception as e:
            print(f"! Warning: Could not generate summary: {str(e)}")
            return "I'm having trouble generating a response. Please try again."

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
                "previous_responses": [],
                "previous_data": [],
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
                            if "sqlQuery" in msg["response"]:
                                chat_context["previous_sql_queries"].append(msg["response"]["sqlQuery"])
                            if "data" in msg["response"]:
                                chat_context["previous_data"].append(msg["response"]["data"])
                            if "insights" in msg["response"]:
                                chat_context["previous_insights"].append(msg["response"]["insights"])
                            # Add the final response that was shown to the user
                            chat_context["previous_responses"].append(msg["response"]["agent_response"])
                except Exception as e:
                    print(f"! Warning: Could not get chat history: {str(e)}")
            
            # Create initial state
            state = AgentState.create_initial_state(question, session_id, client_id)
            state["chat_context"] = chat_context
            
            # Make decision about how to handle the question
            state = await self._make_decision(state)
            
            if state["decision"] == "direct":
                print("\n--- Providing Direct Response ---")
                response_text = await self._generate_summary(state, question)
                response = {
                    "agent_response": response_text
                }
                
                # Add to chat history if session_id is provided
                if session_id:
                    response_to_store = {
                        "agent_response": response["agent_response"]
                    }
                    await self.chat_history.add_message(session_id, question, response_to_store)
            else:
                print("\n--- Using Workflow ---")
                # Create and execute the workflow plan
                print("\nCreating workflow plan...")
                plan = await self.supervisor.create_plan(state, self.model)
                
                print("\nExecuting workflow plan...")
                final_state = await self.supervisor.execute_plan(plan, state)
                
                # Check if there was an error in the workflow
                if final_state["error"] and not final_state["error"]["is_valid"]:
                    error_type = final_state["error"]["error_type"]
                    error_message = final_state["error"]["error_message"]
                    
                    # Create user-friendly error message based on error type
                    user_message = get_user_friendly_error_message(error_type, error_message)
                    
                    response = {
                        "agent_response": user_message,
                        "is_error": True,
                        "error_type": error_type,
                        "error_message": error_message
                    }
                    
                    # Add to chat history if session_id is provided
                    if session_id:
                        response_to_store = {
                            "agent_response": response["agent_response"],
                            "is_error": True,
                            "error_type": error_type,
                            "error_message": error_message
                        }
                        await self.chat_history.add_message(session_id, question, response_to_store)
                    
                    print("\n=== Question Processing Complete with Error ===\n")
                    return response
                
                # Update chat context with final state
                final_state["chat_context"]["workflow_history"].append({
                    "step": final_state["next_step"],
                    "status": final_state["step_status"],
                    "sql_query": final_state["current_sql_query"],
                    "insights": final_state["current_data"]
                })
                
                # Ensure we have the query results in the state
                if "query_results" in final_state:
                    final_state["current_data"] = final_state["query_results"]
                
                # Generate summary from the workflow results
                response_text = await self._generate_summary(final_state, question)
                response = {
                    "agent_response": response_text,
                    "sqlQuery": final_state.get("current_sql_query"),
                    "data": final_state.get("current_data"),
                    "insights": final_state.get("insights")
                }
                
                # Add to chat history if session_id is provided
                if session_id:
                    response_to_store = {
                        "agent_response": response["agent_response"],
                        "sqlQuery": final_state.get("current_sql_query"),
                        "data": final_state.get("current_data"),
                        "insights": final_state.get("insights")
                    }
                    await self.chat_history.add_message(session_id, question, response_to_store)
            
            print("\n=== Question Processing Complete ===\n")
            return response
            
        except Exception as e:
            print(f"\n✗ Error in LoyaltyAgent: {str(e)}")
            error_response = {
                "agent_response": "An unexpected error occurred. Please try again later.",
                "is_error": True,
                "error_type": "unexpected_error",
                "error_message": str(e)
            }
            
            # Add error to chat history if session_id is provided
            if session_id:
                await self.chat_history.add_message(session_id, question, error_response)
            
            return error_response
    
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