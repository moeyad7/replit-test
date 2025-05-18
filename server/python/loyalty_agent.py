import os
import json
import yaml
import requests
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)  # Force override of existing variables
print("Environment variables loaded")
print("OPENAI_API_KEY from env:", os.environ.get("OPENAI_API_KEY"))
print("Current working directory:", os.getcwd())

# Schema type definitions
class TableColumn:
    def __init__(self, name: str, type: str, description: str):
        self.name = name
        self.type = type
        self.description = description
    
    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description
        }

class Table:
    def __init__(self, name: str, description: str, columns: List[TableColumn]):
        self.name = name
        self.description = description
        self.columns = columns
    
    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'columns': [col.to_dict() for col in self.columns]
        }

class DatabaseSchema:
    def __init__(self, tables: List[Table]):
        self.tables = tables
    
    def to_dict(self):
        return {
            'tables': [table.to_dict() for table in self.tables]
        }

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
        self.schema = self._load_database_schema()
        
        print("LoyaltyAgent initialized with LangChain")
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process a natural language question about loyalty program data
        
        Args:
            question: The natural language question to process
            
        Returns:
            A dictionary containing the query understanding, SQL query, results,
            insights, and recommendations
        """
        try:
            print(f"Processing question: {question}")
            
            # Step 1: Generate SQL from the question
            sql_query = self._generate_sql(question)
            print(f"Generated SQL: {sql_query}")
            
            # Step 2: Execute the SQL query
            start_time = time.time()
            query_results, count = self._execute_query(sql_query)
            query_time = time.time() - start_time
            print(f"Query executed, returned {len(query_results)} rows in {query_time:.2f} seconds")
            
            # Step 3: Generate insights from the results
            analysis = self._generate_insights(question, sql_query, query_results)
            print(f"Generated insights: {analysis.get('title', 'No title')}")
            
            # Step 4: Return the complete result
            return {
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
            
        except Exception as e:
            print(f"Error in LoyaltyAgent: {str(e)}")
            
            # Return a fallback response
            return {
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
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the database schema information"""
        return self.schema.to_dict()
    
    def determine_relevant_tables(self, question: str, all_tables: List[Table]) -> List[Table]:
        """
        Determine which tables are relevant to the user's question
        """
        # Create a simple prompt to identify relevant tables
        table_names = [table.name for table in all_tables]
        table_descriptions = {table.name: table.description for table in all_tables}
        
        prompt = f"""Given the user's question about a loyalty program database, identify which tables are needed to answer it.
        
        Available tables:
        {json.dumps(table_descriptions, indent=2)}
        
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
    
    def _generate_sql(self, question: str) -> str:
        """
        Generate SQL from a natural language question
        
        Args:
            question: The natural language question
            
        Returns:
            A SQL query string
        """
        try:
            
            # First determine which tables are relevant
            relevant_tables = self.determine_relevant_tables(question, self.schema.tables)
    
            # Format only the relevant schema for the prompt
            schema_string = self._format_schema_for_prompt(relevant_tables)
            
            # Create prompt for SQL generation
            prompt = f"""You are a SQL expert for a loyalty program database. Your task is to convert natural language questions 
            into SQL queries that can answer the question.
            
            Use the following database schema:
            {schema_string}
            
            Important guidelines:
            1. Only use the tables and columns defined in the schema
            2. Always use proper SQL syntax for the Redshift data warehouse dialect
            3. Include appropriate JOINs when information from multiple tables is needed
            4. Use descriptive aliases for tables (e.g., c for customers, pt for points_transactions)
            5. Limit results to 100 rows unless specified otherwise
            6. Use simple ORDER BY and GROUP BY clauses when appropriate
            7. Format the SQL query nicely with line breaks and proper indentation
            8. Only return a valid SQL query and nothing else
            
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
            mock_data = self._get_mock_data(sql_query)
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
    
    def _load_database_schema(self) -> DatabaseSchema:
        """
        Load database schema from YAML files
        
        Returns:
            DatabaseSchema object
        """
        # Directory for schema files
        schema_dir = Path(__file__).parent.parent / "schema" / "yml"
        tables = []
        
        try:
            # Create directory if it doesn't exist
            schema_dir.mkdir(parents=True, exist_ok=True)
            
            # Get YAML files
            yml_files = list(schema_dir.glob("*.yml")) + list(schema_dir.glob("*.yaml"))
            
            # Create sample files if none exist
            if not yml_files:
                print("No schema files found. Creating sample schema files.")
                self._create_sample_schema_files(schema_dir)
                yml_files = list(schema_dir.glob("*.yml")) + list(schema_dir.glob("*.yaml"))
            
            # Load each schema file
            for file_path in yml_files:
                with open(file_path, "r") as f:
                    table_data = yaml.safe_load(f)
                
                if table_data and "name" in table_data and "columns" in table_data:
                    columns = [
                        TableColumn(
                            name=col["name"],
                            type=col["type"],
                            description=col["description"]
                        )
                        for col in table_data["columns"]
                    ]
                    
                    tables.append(Table(
                        name=table_data["name"],
                        description=table_data["description"],
                        columns=columns
                    ))
                else:
                    print(f"Invalid schema format in file {file_path}")
            
            return DatabaseSchema(tables=tables)
            
        except Exception as e:
            print(f"Error loading database schema: {str(e)}")
            # Return empty schema if there's an error
            return DatabaseSchema(tables=[])
    
    def _format_schema_for_prompt(self, relevant_tables: List[Table]) -> str:
        """
        Format the database schema for inclusion in prompts
        
        Args:
            relevant_tables: List of tables to format in the schema
            
        Returns:
            A formatted string representation of the schema
        """
        result = "DATABASE SCHEMA:\n\n"
        
        for table in relevant_tables:
            result += f"TABLE: {table.name}\n"
            result += f"DESCRIPTION: {table.description}\n"
            result += "COLUMNS:\n"
            
            for column in table.columns:
                result += f"  - {column.name} ({column.type}): {column.description}\n"
            
            result += "\n"
        
        return result
    
    def _create_sample_schema_files(self, directory: Path) -> None:
        """
        Create sample schema files for the loyalty program database
        
        Args:
            directory: Directory to create the files in
        """
        # Customer table schema
        customers_schema = {
            "name": "customers",
            "description": "Contains customer information and their loyalty points",
            "columns": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "Unique identifier for the customer"
                },
                {
                    "name": "first_name",
                    "type": "text",
                    "description": "Customer's first name"
                },
                {
                    "name": "last_name",
                    "type": "text",
                    "description": "Customer's last name"
                },
                {
                    "name": "email",
                    "type": "text",
                    "description": "Customer's email address"
                },
                {
                    "name": "points",
                    "type": "integer",
                    "description": "Current loyalty points balance"
                },
                {
                    "name": "created_at",
                    "type": "timestamp",
                    "description": "Date when the customer joined the loyalty program"
                }
            ]
        }
        
        # Points transactions table schema
        points_transactions_schema = {
            "name": "points_transactions",
            "description": "Records of points earned or redeemed by customers",
            "columns": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "Unique identifier for the transaction"
                },
                {
                    "name": "customer_id",
                    "type": "integer",
                    "description": "Reference to the customer who earned or redeemed points"
                },
                {
                    "name": "points",
                    "type": "integer",
                    "description": "Number of points (positive for earned, negative for redeemed)"
                },
                {
                    "name": "transaction_date",
                    "type": "timestamp",
                    "description": "Date when the transaction occurred"
                },
                {
                    "name": "expiry_date",
                    "type": "timestamp",
                    "description": "Date when the points will expire, if applicable"
                },
                {
                    "name": "source",
                    "type": "text",
                    "description": "Source of the transaction (purchase, referral, redemption, etc.)"
                },
                {
                    "name": "description",
                    "type": "text",
                    "description": "Additional details about the transaction"
                }
            ]
        }
        
        # Challenges table schema
        challenges_schema = {
            "name": "challenges",
            "description": "Marketing challenges that customers can complete to earn bonus points",
            "columns": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "Unique identifier for the challenge"
                },
                {
                    "name": "name",
                    "type": "text",
                    "description": "Name of the challenge"
                },
                {
                    "name": "description",
                    "type": "text",
                    "description": "Details about what customers need to do to complete the challenge"
                },
                {
                    "name": "points",
                    "type": "integer",
                    "description": "Number of points awarded for completing the challenge"
                },
                {
                    "name": "start_date",
                    "type": "timestamp",
                    "description": "Date when the challenge becomes available"
                },
                {
                    "name": "end_date",
                    "type": "timestamp",
                    "description": "Date when the challenge expires"
                },
                {
                    "name": "active",
                    "type": "boolean",
                    "description": "Whether the challenge is currently active"
                }
            ]
        }
        
        # Challenge completions table schema
        challenge_completions_schema = {
            "name": "challenge_completions",
            "description": "Records of challenges completed by customers",
            "columns": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "Unique identifier for the completion record"
                },
                {
                    "name": "customer_id",
                    "type": "integer",
                    "description": "Reference to the customer who completed the challenge"
                },
                {
                    "name": "challenge_id",
                    "type": "integer",
                    "description": "Reference to the challenge that was completed"
                },
                {
                    "name": "completion_date",
                    "type": "timestamp",
                    "description": "Date when the customer completed the challenge"
                },
                {
                    "name": "points_awarded",
                    "type": "integer",
                    "description": "Number of points awarded for completing the challenge"
                }
            ]
        }
        
        try:
            # Write schema files
            with open(directory / "customers.yml", "w") as f:
                yaml.dump(customers_schema, f)
                
            with open(directory / "points_transactions.yml", "w") as f:
                yaml.dump(points_transactions_schema, f)
                
            with open(directory / "challenges.yml", "w") as f:
                yaml.dump(challenges_schema, f)
                
            with open(directory / "challenge_completions.yml", "w") as f:
                yaml.dump(challenge_completions_schema, f)
                
            print(f"Created sample schema files in {directory}")
            
        except Exception as e:
            print(f"Error creating sample schema files: {str(e)}")
    
    def _get_mock_data(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Get mock data based on the SQL query
        
        Args:
            sql_query: The SQL query string
            
        Returns:
            A list of mock data records
        """
        # Determine which mock data to return based on the query
        sql_lower = sql_query.lower()
        
        if "points_transactions" in sql_lower or "transaction" in sql_lower:
            return self._get_mock_transactions()
        elif "challenges" in sql_lower and "challenge_completions" not in sql_lower:
            return self._get_mock_challenges()
        elif "challenge_completions" in sql_lower or "completion" in sql_lower:
            return self._get_mock_challenge_completions()
        else:
            return self._get_mock_customers()
    
    def _get_mock_customers(self) -> List[Dict[str, Any]]:
        """Get mock customer data"""
        return [
            {"id": 1, "first_name": "Michael", "last_name": "Scott", "email": "mscott@example.com", "points": 3542, "created_at": "2023-01-15"},
            {"id": 2, "first_name": "Jim", "last_name": "Halpert", "email": "jhalpert@example.com", "points": 2891, "created_at": "2023-01-20"},
            {"id": 3, "first_name": "Pam", "last_name": "Beesly", "email": "pbeesly@example.com", "points": 2745, "created_at": "2023-01-22"},
            {"id": 4, "first_name": "Dwight", "last_name": "Schrute", "email": "dschrute@example.com", "points": 2103, "created_at": "2023-02-01"},
            {"id": 5, "first_name": "Kelly", "last_name": "Kapoor", "email": "kkapoor@example.com", "points": 1986, "created_at": "2023-02-15"}
        ]
    
    def _get_mock_transactions(self) -> List[Dict[str, Any]]:
        """Get mock transaction data"""
        return [
            {"id": 1, "customer_id": 1, "points": 500, "transaction_date": "2023-05-01", "expiry_date": "2024-05-01", "source": "purchase", "description": "Online purchase"},
            {"id": 2, "customer_id": 1, "points": 200, "transaction_date": "2023-05-15", "expiry_date": "2024-05-15", "source": "referral", "description": "Friend referral"},
            {"id": 3, "customer_id": 2, "points": 350, "transaction_date": "2023-05-05", "expiry_date": "2024-05-05", "source": "purchase", "description": "In-store purchase"},
            {"id": 4, "customer_id": 3, "points": -150, "transaction_date": "2023-05-20", "expiry_date": None, "source": "redemption", "description": "Gift card redemption"},
            {"id": 5, "customer_id": 4, "points": 425, "transaction_date": "2023-05-10", "expiry_date": "2024-05-10", "source": "purchase", "description": "Mobile app purchase"}
        ]
    
    def _get_mock_challenges(self) -> List[Dict[str, Any]]:
        """Get mock challenge data"""
        return [
            {"id": 1, "name": "Summer Bonus", "description": "Make 3 purchases in June", "points": 500, "start_date": "2023-06-01", "end_date": "2023-06-30", "active": True},
            {"id": 2, "name": "Referral Drive", "description": "Refer a friend to join our program", "points": 300, "start_date": "2023-05-01", "end_date": "2023-07-31", "active": True},
            {"id": 3, "name": "Social Media", "description": "Share your purchase on social media", "points": 150, "start_date": "2023-04-15", "end_date": "2023-08-15", "active": True},
            {"id": 4, "name": "First Purchase", "description": "Complete your first purchase", "points": 200, "start_date": "2023-01-01", "end_date": "2023-12-31", "active": True},
            {"id": 5, "name": "Loyalty Anniversary", "description": "Celebrate your 1-year membership", "points": 500, "start_date": "2023-01-01", "end_date": "2023-12-31", "active": True}
        ]
    
    def _get_mock_challenge_completions(self) -> List[Dict[str, Any]]:
        """Get mock challenge completion data"""
        return [
            {"id": 1, "customer_id": 1, "challenge_id": 1, "completion_date": "2023-06-15", "points_awarded": 500},
            {"id": 2, "customer_id": 1, "challenge_id": 4, "completion_date": "2023-01-20", "points_awarded": 200},
            {"id": 3, "customer_id": 2, "challenge_id": 2, "completion_date": "2023-05-25", "points_awarded": 300},
            {"id": 4, "customer_id": 3, "challenge_id": 3, "completion_date": "2023-05-10", "points_awarded": 150},
            {"id": 5, "customer_id": 5, "challenge_id": 4, "completion_date": "2023-02-18", "points_awarded": 200}
        ]