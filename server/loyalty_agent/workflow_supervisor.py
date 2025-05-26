from typing import Dict, Any, List, Optional, Callable, Awaitable
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StepStatus(Enum):
    SUCCESS = "success"
    RETRY = "retry"
    ERROR = "error"
    COMPLETE = "complete"

class WorkflowSupervisor:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.step_retries: Dict[str, int] = {}
    
    async def supervise_step(
        self,
        step_name: str,
        step_func: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        state: Dict[str, Any],
        next_step: Optional[str] = None,
        error_step: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Supervise a workflow step with retry logic and routing
        
        Args:
            step_name: Name of the current step
            step_func: Async function to execute the step
            state: Current workflow state
            next_step: Name of the next step on success
            error_step: Name of the step to go to on unrecoverable error
            
        Returns:
            Updated state with routing information
        """
        try:
            # Initialize retry count for this step if not exists
            if step_name not in self.step_retries:
                self.step_retries[step_name] = 0
            
            # Execute the step
            logger.info(f"Executing step: {step_name}")
            updated_state = await step_func(state)
            
            # First check if step was successful
            if self._is_step_successful(updated_state):
                logger.info(f"Step {step_name} completed successfully")
                self.step_retries[step_name] = 0  # Reset retry count
                updated_state["next_step"] = next_step
                updated_state["step_status"] = StepStatus.SUCCESS
                return updated_state
            
            # If step failed, check if we should retry
            if self._should_retry_step(step_name, updated_state):
                logger.info(f"Retrying step {step_name} (attempt {self.step_retries[step_name] + 1}/{self.max_retries})")
                self.step_retries[step_name] += 1
                updated_state["step_status"] = StepStatus.RETRY
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
            logger.error(f"Step {step_name} failed with error: {error_type} - {error_message}")
            updated_state["next_step"] = error_step
            updated_state["step_status"] = StepStatus.ERROR
            updated_state["error"] = {
                "is_valid": False,
                "error_message": f"Failed in step '{step_name}': {error_message}",
                "error_type": error_type,
                "failed_step": step_name
            }
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in step {step_name}: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": f"Failed in step '{step_name}': {str(e)}",
                "error_type": f"{step_name}_error",
                "failed_step": step_name
            }
            state["next_step"] = error_step
            state["step_status"] = StepStatus.ERROR
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
                logger.info(f"Query execution failed with error, retrying from SQL generation")
                state["next_step"] = "generate_sql"  # Go back to SQL generation
                return True
            elif state.get("sql_query") and not state.get("data"):
                logger.info(f"Query returned no data when data was expected, retrying from SQL generation")
                state["next_step"] = "generate_sql"  # Go back to SQL generation
                return True
                
        elif step_name == "validate_response":
            # If response validation fails, retry from the beginning
            if state.get("error") and not state["error"].get("is_valid", True) and state["error"].get("needs_retry", True):
                logger.info(f"Response validation failed, retrying from beginning")
                state["next_step"] = "generate_sql"  # Go back to SQL generation
                return True
            
        return False
    
    def is_workflow_complete(self, state: Dict[str, Any]) -> bool:
        """Check if the workflow has all required information to be complete"""
        required_fields = [
            "sql_query",
            "data",
            "insights",
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