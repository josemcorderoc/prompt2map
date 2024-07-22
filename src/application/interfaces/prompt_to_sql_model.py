from typing import Protocol


class PromptToSQLModel(Protocol):
    def to_sql(self, prompt: str) -> str:
        ...