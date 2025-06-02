from typing import Dict, Any, List, Optional, TypedDict
from enum import Enum
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import json

from .config.prompts import WorkflowPrompts
from .utils.error_handling import create_error_response

logger = logging.getLogger(__name__)

# Tool descriptions as a constant
TOOL_DESCRIPTIONS = {
    "security_validator": "Validates input and SQL for security concerns",
    "sql_generator": "Generates SQL queries from natural language questions",
    "query_executor": "Executes SQL queries against the database",
    "insights_generator": "Generates insights and recommendations from query results"
}

class StepStatus(Enum):
    SUCCESS = "success"
    RETRY = "retry"
    ERROR = "error"
    COMPLETE = "complete"

class PlanStep(TypedDict):
    step_name: str
    tool_name: str
    description: str
    next_step: Optional[str]
    error_step: Optional[str]

class WorkflowSupervisor:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.step_retries: Dict[str, int] = {}
        self.available_tools = {}  # Will be populated with actual tool instances
    
    def set_tools(self, tools: Dict[str, Any]):
        """Set the available tools for the workflow"""
        self.available_tools = tools
    
    async def create_plan(self, state: Dict[str, Any], model: ChatOpenAI) -> List[PlanStep]:
        """Create a plan of steps to execute based on the current state and question"""
        print("\n--- Creating Workflow Plan ---")
        try:
            question = state["question"]
            prompt = WorkflowPrompts.get_workflow_plan_prompt(
                question=question,
                tools_description=TOOL_DESCRIPTIONS,
                chat_context=state.get('chat_context', {})
            )
            
            print("Generating workflow plan...")
            response = await model.ainvoke([HumanMessage(content=prompt)])
            
            try:
                # Clean and parse the response
                content = response.content.strip()
                content = content.replace('```json', '').replace('```', '').strip()
                plan = json.loads(content)
                
                if not isinstance(plan, list):
                    raise ValueError("Plan must be a list of steps")
                
                # Validate the plan
                self._validate_plan(plan)
                
                print(f"✓ Generated plan with {len(plan)} steps")
                return plan
                
            except Exception as parse_error:
                print(f"✗ Error parsing plan JSON: {str(parse_error)}")
                raise ValueError(f"Failed to parse workflow plan: {str(parse_error)}")
                
        except Exception as e:
            print(f"✗ Error creating workflow plan: {str(e)}")
            raise ValueError(f"Failed to create workflow plan: {str(e)}")
    
    def _validate_plan(self, plan: List[PlanStep]) -> None:
        """Validate that the plan meets our requirements"""
        # Check if plan is empty
        if not plan:
            raise ValueError("Plan cannot be empty")
        
        # Check if first step is security validation
        if plan[0]["tool_name"] != "security_validator":
            raise ValueError("First step must be security validation")
        
        # Check if SQL generation and execution are present
        has_sql_generation = False
        has_query_execution = False
        
        for step in plan:
            if step["tool_name"] == "sql_generator":
                has_sql_generation = True
            elif step["tool_name"] == "query_executor":
                has_query_execution = True
        
        # SQL generation is only required if we're executing a query
        if has_query_execution and not has_sql_generation:
            raise ValueError("Query execution requires SQL generation")
        
        # Validate step dependencies
        for i, step in enumerate(plan):
            # SQL generation must come before query execution
            if step["tool_name"] == "query_executor":
                sql_generation_before = any(
                    prev_step["tool_name"] == "sql_generator"
                    for prev_step in plan[:i]
                )
                if not sql_generation_before:
                    raise ValueError("Query execution must come after SQL generation")
    
    async def execute_plan(self, plan: List[PlanStep], state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow plan step by step"""
        print("\n--- Executing Workflow Plan ---")
        print("\nPlan details:")
        for i, step in enumerate(plan):
            print(f"Step {i + 1}: {step['step_name']} using {step['tool_name']}")
            print(f"  Description: {step['description']}")
            print(f"  Next step: {step['next_step']}")
        
        current_step_index = 0
        while current_step_index < len(plan):
            step = plan[current_step_index]
            print(f"\nExecuting step {current_step_index + 1}/{len(plan)}: {step['step_name']}")
            
            try:
                # Get the tool for this step
                tool = self.available_tools.get(step['tool_name'])
                if not tool:
                    raise ValueError(f"Tool {step['tool_name']} not found")
                
                # Map tool names to their methods
                tool_methods = {
                    "security_validator": "validate_input",
                    "sql_generator": "generate_sql",
                    "query_executor": "execute_query",
                    "insights_generator": "generate_insights"
                }
                
                # Get the method to call
                method_name = tool_methods.get(step['tool_name'])
                if not method_name:
                    raise ValueError(f"No method mapping found for tool {step['tool_name']}")
                
                # Get the method from the tool
                method = getattr(tool, method_name)
                if not callable(method):
                    raise ValueError(f"Method {method_name} is not callable on tool {step['tool_name']}")
                
                # Execute the step
                state = await self._execute_step(step, state, method)
                 
                # Check if we need to retry
                if state.get("step_status") == StepStatus.RETRY.value:
                    if self._should_retry_step(step['step_name'], state):
                        print(f"Retrying step {step['step_name']}")
                        continue
                    else:
                        print(f"Max retries exceeded for step {step['step_name']}")
                        return create_error_response(state)
                
                # Check if we need to handle an error
                if state.get("step_status") == StepStatus.ERROR.value:
                    return create_error_response(state)
                
                # Check if this is the last step
                if current_step_index == len(plan) - 1:
                    print("✓ Workflow completed successfully")
                    state["step_status"] = StepStatus.COMPLETE.value
                    return state
                
                # Move to next step
                current_step_index += 1
                
            except Exception as e:
                print(f"✗ Error executing step {step['step_name']}: {str(e)}")
                state["error"] = {
                    "is_valid": False,
                    "error_message": str(e),
                    "error_type": f"{step['step_name']}_error"
                }
                return create_error_response(state)
        
        return state
    
    async def _execute_step(self, step: PlanStep, state: Dict[str, Any], tool: Any) -> Dict[str, Any]:
        """Execute a single step of the plan"""
        try:
            # Initialize retry count for this step if not exists
            if step['step_name'] not in self.step_retries:
                self.step_retries[step['step_name']] = 0
            
            # Execute the step
            logger.info(f"Executing step: {step['step_name']}")
            updated_state = await tool(state)
            
            # Update chat context with tool response
            if "chat_context" not in updated_state:
                updated_state["chat_context"] = {}
            
            # Store tool response in chat context based on tool type
            if step['tool_name'] == "sql_generator":
                if "current_sql_query" in updated_state:
                    updated_state["chat_context"]["previous_sql_queries"] = updated_state["chat_context"].get("previous_sql_queries", [])
                    updated_state["chat_context"]["previous_sql_queries"].append(updated_state["current_sql_query"])
            
            elif step['tool_name'] == "query_executor":
                if "current_data" in updated_state:
                    # Store the data in both current_data and query_results
                    updated_state["query_results"] = updated_state["current_data"]
                    updated_state["chat_context"]["previous_data"] = updated_state["chat_context"].get("previous_data", [])
                    updated_state["chat_context"]["previous_data"].append(updated_state["current_data"])
            
            elif step['tool_name'] == "insights_generator":
                if "insights" in updated_state:
                    updated_state["chat_context"]["previous_insights"] = updated_state["chat_context"].get("previous_insights", [])
                    updated_state["chat_context"]["previous_insights"].append(updated_state["insights"])
            
            # Check if step was successful
            if self._is_step_successful(updated_state):
                logger.info(f"Step {step['step_name']} completed successfully")
                self.step_retries[step['step_name']] = 0  # Reset retry count
                updated_state["next_step"] = step['next_step']
                updated_state["step_status"] = StepStatus.SUCCESS.value  # Store the string value
                return updated_state
            
            # If step failed, check if we should retry
            if self._should_retry_step(step['step_name'], updated_state):
                logger.info(f"Retrying step {step['step_name']} (attempt {self.step_retries[step['step_name']] + 1}/{self.max_retries})")
                self.step_retries[step['step_name']] += 1
                updated_state["step_status"] = StepStatus.RETRY.value  # Store the string value
                # Clear the error state when retrying
                updated_state["error"] = {
                    "is_valid": True,
                    "error_message": None,
                    "error_type": None
                }
                return updated_state
            
            # If we get here, the step failed and shouldn't be retried
            error_info = updated_state.get("error", {})
            error_type = error_info.get("error_type", "unknown_error")
            error_message = error_info.get("error_message", "Unknown error occurred")
            logger.error(f"Step {step['step_name']} failed with error: {error_type} - {error_message}")
            
            # Set error state without exposing error_step
            updated_state["step_status"] = StepStatus.ERROR.value
            updated_state["error"] = {
                "is_valid": False,
                "error_message": f"Failed in step '{step['step_name']}': {error_message}",
                "error_type": error_type,
                "failed_step": step['step_name']
            }
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in step {step['step_name']}: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": f"Failed in step '{step['step_name']}': {str(e)}",
                "error_type": f"{step['step_name']}_error",
                "failed_step": step['step_name']
            }
            state["step_status"] = StepStatus.ERROR.value
            return state
    
    def _is_step_successful(self, state: Dict[str, Any]) -> bool:
        """Check if a step was successful based on state"""
        # Only fail if is_valid is explicitly False
        if state.get("error"):
            if state["error"].get("is_valid") is False:
                logger.error(f"Step failed with error: {state['error'].get('error_type')} - {state['error'].get('error_message')}")
                return False
        return True
    
    def _should_retry_step(self, step_name: str, state: Dict[str, Any]) -> bool:
        """Determine if a step should be retried"""
        # Check if we've exceeded max retries
        if self.step_retries[step_name] >= self.max_retries:
            logger.info(f"Max retries ({self.max_retries}) exceeded for step {step_name}")
            return False
        
        # Check step-specific retry conditions
        if step_name == "validate_input":
            # If input validation fails due to a temporary error, retry
            if state.get("error") and state["error"].get("is_valid", False):
                logger.info(f"Input validation failed, retrying")
                return True
                
        elif step_name == "execute_query":
            # Only retry if there's an explicit error or no data when we expect data
            if state.get("error") and state["error"].get("is_valid") is False:
                logger.info(f"Query execution failed with error, retrying")
                return True
            elif state.get("sql_query") and not state.get("data"):
                logger.info(f"Query returned no data when data was expected, retrying")
                return True
            
        return False
    
    def is_workflow_complete(self, state: Dict[str, Any]) -> bool:
        """Check if the workflow has all required information to be complete"""
        required_fields = [
            "sql_query",
            "data",
            "result_count",
            "query_time"
        ]
        
        # Check if all required fields are present and valid
        for field in required_fields:
            if field not in state or state[field] is None:
                return False
        
        # Check if there are no errors
        if state.get("error"):
            return False
        
        print("All finished")
        return True 