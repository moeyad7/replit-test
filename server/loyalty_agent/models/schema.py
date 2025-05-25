from typing import List, Dict, Any, Optional

class TableColumn:
    def __init__(self, name: str, type: str, description: str, properties: Optional[Dict[str, Any]] = None):
        self.name = name
        self.type = type
        self.description = description
        # Ensure properties is always a dictionary
        if properties is None:
            self.properties = {}
        elif isinstance(properties, dict):
            self.properties = properties
        elif isinstance(properties, list):
            # Convert list to dict if it's a list of key-value pairs
            try:
                self.properties = dict(properties)
            except (ValueError, TypeError):
                self.properties = {}
        else:
            self.properties = {}

    def to_dict(self):
        column_dict = {
            'name': self.name,
            'type': self.type,
            'description': self.description
        }
        if self.properties:
            column_dict['properties'] = self.properties
        return column_dict

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