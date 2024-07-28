from email import message
from pyexpat.errors import messages
from typing import Any, Optional
import jsonlines
import numpy as np
from openai import OpenAI
from openai.types import Batch

from application.interfaces.embedding import Embedding
from application.interfaces.llm import LLM

def generate_openai_embedding_request(id: int, text: str) -> dict:
    return {
        "custom_id": f"embedding_request_{id}",
        "method": "POST",
        "url": "/v1/embeddings",
        "body": {
            "input": text,
            "model": "text-embedding-3-small",
        }
    }
    
def generate_openai_completion_request(id: int, system_prompt: Optional[str] = None, user_prompt: Optional[str] = None) -> dict:
    messages = get_messages(system_prompt, user_prompt)
    return {
        "custom_id": f"request-{id}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": 10
        }
    }
def get_messages(system_prompt: Optional[str] = None, user_prompt: Optional[str] = None) -> list[dict[str, str]]:
    messages = []
    if system_prompt is None and user_prompt is None:
        raise ValueError("At least one of system_prompt or user_prompt must be provided")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})
    return messages

class GPT4(LLM, Embedding):
    def __init__(self, model_name="gpt-4o", embedding_model_name='text-embedding-3-small') -> None:
        self.client = OpenAI()
        self.model_name = model_name
        self.embedding_model_name = embedding_model_name
        
    def chat(self, user_prompt: Optional[str], system_prompt: Optional[str]) -> str:
        messages = get_messages(system_prompt, user_prompt)
            
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
        messages = get_messages(system_prompt, user_prompt)
            
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages, # type: ignore
            tools=tools, # type: ignore
            tool_choice=tool_choice # type: ignore
        )
        return response.choices[0].message.tool_calls
    
    def get_embedding(self, text: str) -> np.ndarray:
        embedding = self.client.embeddings.create(
            input=[text],
            model=self.embedding_model_name
        ).data[0].embedding
        return np.array(embedding)
    
    
    def send_batch_embedding(self, requests, input_file_name: str) -> str:
        # Write the requests to a jsonl file7
        with jsonlines.open(input_file_name, mode='w') as writer:
            writer.write_all(requests)
        
        # Register file in OpenAI
        batch_input_file = self.client.files.create(
            file=open(input_file_name, "rb"),
            purpose="batch"
        )
        
        # Send the batch to OpenAI
        openai_batch = self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/embeddings",
            completion_window="24h",
            metadata={
                "description": "testing",
            }
        )
        return openai_batch.id

    def get_batch(self, batch_id: str) -> Batch:
        return self.client.batches.retrieve(batch_id)

    def get_batch_result(self, output_file_id: str, output_path: str):
        content = self.client.files.content(output_file_id)
        content.write_to_file(output_path)