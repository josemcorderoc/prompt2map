from typing import Optional
from application.interfaces.llm import LLM
from application.interfaces.prompt_to_sql_model import PromptToSQLModel
from infrastructure.gpt4 import GPT4
import re


class LLMToSQL(PromptToSQLModel):
    def __init__(self, llm: LLM, db_schema: Optional[str] = None) -> None:
        self.system_prompt = "You are a helpful assistant designed to receive a question as input and return a valid SQL query that retrieves the data to answer that question. Always use GROUP BY. Do not use integer literals."
        if db_schema:
            self.system_prompt += f" Use the following database schema as basis:\n<schema>{db_schema}</schema>"
        self.user_prompt_template = "Write a SQL query that answer this question :\n<question>{question}</question>"

        self.llm = llm

    def to_sql(self, prompt: str) -> str:
        response = self.llm.chat(self.user_prompt_template.format(
            question=prompt), self.system_prompt)
        regex_pattern = r"```sql([\s\S]*)```"
        match = re.search(regex_pattern, response)
        if match:
            return match.group(1)
        return response
