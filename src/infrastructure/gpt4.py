from email import message
from pyexpat.errors import messages
from typing import Any, Optional
import numpy as np
from openai import OpenAI

from application.interfaces.embedding import Embedding
from application.interfaces.llm import LLM

class GPT4(LLM, Embedding):
    def __init__(self, model_name="gpt-4o", emnbedding_model_name='text-embedding-3-small') -> None:
        self.client = OpenAI()
        self.model_name = model_name
        self.emnbedding_model_name = emnbedding_model_name
        
    def chat(self, user_prompt: Optional[str], system_prompt: Optional[str]) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "user", "content": user_prompt})
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
            
        response = self.client.chat.completions.create(
            model=self.model_name,
            response_format={ "type": "text" },
            messages=messages # type: ignore
        )
        output = response.choices[0].message.content
        if output:
            return output
        raise ValueError("No response from GPT4Chat")
    
    def function_calling(self, user_prompt: Optional[str], system_prompt: Optional[str], tools: list[dict], tool_choice: str = "auto") -> Optional[list[Any]] :
        messages = []
        if system_prompt:
            messages.append({"role": "user", "content": user_prompt})
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
            
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools, # type: ignore
            tool_choice=tool_choice
        )
        return response.choices[0].message.tool_calls
    
    def get_embedding(self, text: str) -> np.ndarray:
        embedding = self.client.embeddings.create(
            input=[text],
            model=self.emnbedding_model_name
        ).data[0].embedding
        return np.array(embedding)