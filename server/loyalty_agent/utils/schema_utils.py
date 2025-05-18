import yaml
from pathlib import Path
from typing import List
from ..models.schema import Table, TableColumn, DatabaseSchema

def load_database_schema() -> DatabaseSchema:
    """
    Load database schema from YAML files.

    Returns:
        DatabaseSchema object
    """
    schema_dir = Path(__file__).parent.parent.parent / "schema" / "yml"
    tables = []

    try:
        schema_dir.mkdir(parents=True, exist_ok=True)
        yml_files = list(schema_dir.glob("*.yml")) + list(schema_dir.glob("*.yaml"))

        if not yml_files:
            print("No schema files found. Creating sample schema files.")
            create_sample_schema_files(schema_dir)
            yml_files = list(schema_dir.glob("*.yml")) + list(schema_dir.glob("*.yaml"))

        for file_path in yml_files:
            with open(file_path, "r") as f:
                table_data = yaml.safe_load(f)

            if table_data and "name" in table_data and "columns" in table_data:
                columns = []
                for col in table_data["columns"]:
                    column = TableColumn(
                        name=col["name"],
                        type=col["type"],
                        description=col["description"],
                        properties=col.get("properties")  # Optional field
                    )
                    columns.append(column)

                table = Table(
                    name=table_data["name"],
                    description=table_data.get("description", ""),
                    columns=columns
                )
                tables.append(table)
            else:
                print(f"Invalid schema format in file {file_path}")

        return DatabaseSchema(tables=tables)

    except Exception as e:
        print(f"Error loading database schema: {str(e)}")
        return DatabaseSchema(tables=[])

def format_schema_for_prompt(relevant_tables: List[Table]) -> str:
    """
    Format the database schema for inclusion in prompts.

    Args:
        relevant_tables: List of tables to format in the schema.

    Returns:
        A formatted string representation of the schema.
    """
    result = "DATABASE SCHEMA:\n\n"

    for table in relevant_tables:
        result += f"TABLE: {table.name}\n"
        result += f"DESCRIPTION: {table.description}\n"
        result += "COLUMNS:\n"

        for column in table.columns:
            line = f"  - {column.name} ({column.type}): {column.description}"
            if column.properties:
                props = ", ".join(f"{k}={v}" for k, v in column.properties.items())
                line += f" [{props}]"
            result += line + "\n"

        result += "\n"

    return result

def create_sample_schema_files(directory: Path) -> None:
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
        