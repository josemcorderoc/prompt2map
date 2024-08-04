from typing import Protocol


class Prompt2SQL(Protocol):
    def to_sql(self, prompt: str) -> str:
        ...