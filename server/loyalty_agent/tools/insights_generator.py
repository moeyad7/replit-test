from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import json

class InsightsGeneratorTool:
    def __init__(self, model: ChatOpenAI):
        self.model = model

    async def generate_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from query results"""
        print("\n--- Generating Insights ---")
        try:
            question = state["question"]
            sql_query = state["sql_query"]
            data = state["data"]
            
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
            
            print("Generating insights from query results...")
            response = await self.model.ainvoke([HumanMessage(content=prompt)])
            
            # Extract and parse the JSON from the response
            try:
                response_text = response.content.strip()
                # Find JSON in the response (in case it contains additional text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    analysis = json.loads(json_str)
                    print(f"✓ Generated insights with title: {analysis.get('title', 'No title')}")
                    return analysis
                else:
                    raise ValueError("No valid JSON found in response")
                    
            except Exception as parse_error:
                print(f"✗ Error parsing insights JSON: {str(parse_error)}")
                return await self._create_fallback_insights()
                
        except Exception as e:
            print(f"✗ Error generating insights: {str(e)}")
            return await self._create_fallback_insights()
    
    async def _create_fallback_insights(self) -> Dict[str, Any]:
        """Create fallback insights when generation fails"""
        print("Creating fallback insights...")
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