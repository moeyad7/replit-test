from typing import List, Dict, Any

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