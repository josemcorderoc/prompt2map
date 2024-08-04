from typing import Protocol


class LLM(Protocol):
    def chat(self, user_prompt: str, system_prompt: str) -> str:
        ...