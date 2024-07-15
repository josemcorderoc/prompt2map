from typing import Protocol


class SQLModel(Protocol):
    def to_sql(self, prompt: str) -> str:
        ...