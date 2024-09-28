import inspect
import json
import logging
from typing import Any, Callable, Iterable, Literal, Optional, TypeVar
from duckdb import DEFAULT
import jsonlines
import numpy as np
from openai.types import Batch
from openai import OpenAI

from prompt2map.interfaces.nlp.embedding import Embedding
from prompt2map.interfaces.nlp.llm import LLM

T = TypeVar('T')

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_LLM_MODEL = "gpt-4o"

def generate_openai_embedding_request(id: int, text: str, model: str = DEFAULT_EMBEDDING_MODEL) -> dict:
    return {
        "custom_id": f"embedding_request_{id}",
        "method": "POST",
        "url": "/v1/embeddings",
        "body": {
            "input": text,
            "model": model,
        }
    }
    
def generate_openai_completion_request(id: int, max_tokens: int, system_prompt: Optional[str] = None, user_prompt: Optional[str] = None, model: str = DEFAULT_LLM_MODEL) -> dict:
    messages = get_messages(system_prompt, user_prompt)
    return {
        "custom_id": f"request-{id}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": DEFAULT_LLM_MODEL,
            "messages": messages,
            "max_tokens": max_tokens
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

class OpenAIProvider(LLM, Embedding):
    def __init__(self, model_name: str = DEFAULT_LLM_MODEL, embedding_model_name: str = DEFAULT_EMBEDDING_MODEL, api_key: Optional[str] = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = OpenAI(api_key=api_key)
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
    
    def function_calling_python(self, user_prompt: Optional[str], system_prompt: Optional[str], functions: dict[str, Callable[..., T]], tools: list[dict], tool_choice: str = "auto", **kwargs) -> Optional[T]:
        # tools = get_available_tools(data)
        tool_calls = self.function_calling(user_prompt, system_prompt, tools, tool_choice)
        if tool_calls is None or len(tool_calls) == 0:
            self.logger.error("No tool calls found")
            return None
        self.logger.info(f"Tool calls: {tool_calls}")
        
        tool_call = tool_calls[0]  # TODO: Select the best tool call 
        self.logger.info(f"Selected tool call: {tool_call}")
        
        function_name = tool_call.function.name
        tool_match = next((tool for tool in tools if tool["function"]["name"] == function_name), None)
        if tool_match is None:
            return None
        function_to_call = functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        self.logger.info(f"Function args: {function_args}")
        
        function_args |= kwargs
        self.logger.info(f"Function args merged with kwargs {list(kwargs.keys())}")

        function_response = function_to_call(
            **{key: value for key, value in function_args.items() if key in inspect.signature(function_to_call).parameters}
        )
        return function_response
    
    def get_embedding(self, text: str) -> np.ndarray:
        embedding = self.client.embeddings.create(
            input=[text],
            model=self.embedding_model_name
        ).data[0].embedding
        return np.array(embedding)
    
    
    def send_batch(self, requests: Iterable[dict], input_file_name: str, endpoint: Literal["/v1/chat/completions", "/v1/embeddings", "/v1/completions"]) -> str:
        # Write the requests to a jsonl file
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
            endpoint=endpoint,
            completion_window="24h",
            metadata={
                "description": "testing",
            }
        )
        return openai_batch.id

    def get_batch(self, batch_id: str) -> Batch:
        return self.client.batches.retrieve(batch_id)

    def get_batch_result(self, output_file_id: str, output_path: Optional[str] = None) -> list[dict]:
        content = self.client.files.content(output_file_id)
        if output_path:
            content.write_to_file(output_path)
        return list(map(json.loads, content.iter_lines()))