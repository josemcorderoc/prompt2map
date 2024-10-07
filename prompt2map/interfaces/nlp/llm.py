from typing import Callable, Optional, Protocol

from prompt2map.types import T


class LLM(Protocol):
    def chat(self, user_prompt: str, system_prompt: str) -> str:
        ...
        
    def function_calling(self, user_prompt: Optional[str], system_prompt: Optional[str], functions: dict[str, Callable[..., T]], tools: list[dict], tool_choice: str = "auto", **kwargs) -> Optional[T]:
        ...