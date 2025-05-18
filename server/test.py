from loyalty_agent.utils.schema_utils import load_database_schema, format_schema_for_prompt


print(format_schema_for_prompt(load_database_schema().tables))

