from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import json
import logging

from ..config.prompts import ToolPrompts

logger = logging.getLogger(__name__)

class InsightsGeneratorTool:
    """Tool for generating insights from query results"""
    
    def __init__(self, model: ChatOpenAI):
        self.model = model
    
    async def generate_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from the query results"""
        try:
            question = state["question"]
            sql_query = state["current_sql_query"]
            data = state["current_data"]
            chat_context = state.get("chat_context", {})
            
            # Create prompt for insights generation
            prompt = ToolPrompts.get_insights_generator_prompt(
                question=question,
                sql_query=sql_query,
                data=data,
                chat_context=chat_context
            )
            
            print("Generating insights from query results...")
            response = await self.model.ainvoke([HumanMessage(content=prompt)])
            
            # Extract and parse the JSON from the response
            try:
                # Get the content from the response
                response_text = response.content if hasattr(response, 'content') else str(response)
                response_text = response_text.strip()
                                
                # Find JSON in the response (in case it contains additional text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    analysis = json.loads(json_str)
                    print(f"✓ Generated insights with title: {analysis.get('title', 'No title')}")
                    state["insights"] = analysis
                    return state
                else:
                    raise ValueError("No valid JSON found in response")
                    
            except Exception as parse_error:
                logger.error(f"Error parsing insights response: {str(parse_error)}")
                state["error"] = {
                    "is_valid": False,
                    "error_message": f"Failed to parse insights response: {str(parse_error)}",
                    "error_type": "insights_parse_error"
                }
                return state
                
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            state["error"] = {
                "is_valid": False,
                "error_message": f"Failed to generate insights: {str(e)}",
                "error_type": "insights_generation_error"
            }
            return state