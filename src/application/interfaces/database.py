from typing import Protocol


class Database(Protocol):
    def run_query(self, query: str) -> list[dict]:
        ...
        
    def get_schema(self) -> str:
        ...
        