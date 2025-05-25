import yaml
from pathlib import Path
from typing import List, Dict
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

        for file_path in yml_files:
            with open(file_path, "r") as f:
                table_data = yaml.safe_load(f)

            if table_data and "name" in table_data and "columns" in table_data:
                columns = []
                for col in table_data["columns"]:
                    # Check for required fields
                    if not all(key in col for key in ["name", "description"]):
                        print(f"Warning: Skipping column in {file_path} - missing required fields (name or description)")
                        continue
                        
                    column = TableColumn(
                        name=col["name"],
                        type=col.get("type"),  # Optional field without default value
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

def get_table_name_description() -> Dict[str, str]:
    """
    Get a dictionary mapping table names to their descriptions.

    Returns:
        Dict[str, str]: Dictionary with table names as keys and descriptions as values
    """
    try:
        schema = load_database_schema()
        return {table.name: table.description for table in schema.tables}
    except Exception as e:
        print(f"Error getting table descriptions: {str(e)}")
        return {}


def format_schema_for_prompt(table_names: List[str]) -> str:
    """
    Format the schema for given table names into a readable string for prompting.

    Args:
        table_names (List[str]): List of table names to include in the output.

    Returns:
        str: A formatted string describing the tables and their columns.
    """
    schema = load_database_schema()
    table_map = {table.name: table for table in schema.tables}
    output_lines = []

    for table_name in table_names:
        table = table_map.get(table_name)
        if not table:
            print(f"Warning: Table '{table_name}' not found in schema")
            output_lines.append(f"⚠️ Table '{table_name}' not found in schema.\n")
            continue

        output_lines.append(f"📘 **Table: {table.name}**")
        output_lines.append(f"Description: {table.description or 'No description provided.'}")
        output_lines.append("Columns:")

        for column in table.columns:
            column_line = f"  - {column.name} ({column.type or 'unknown'}): {column.description}"
            if column.properties:
                try:
                    props = ", ".join(f"{k}={v}" for k, v in column.properties.items())
                    column_line += f" [properties: {props}]"
                except Exception as e:
                    print(f"Error processing properties for column {column.name}: {str(e)}")
            output_lines.append(column_line)

        output_lines.append("")  # Add a blank line between tables

    return "\n".join(output_lines)