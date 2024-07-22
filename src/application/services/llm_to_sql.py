from typing import Optional
from application.interfaces.llm import LLM
from application.interfaces.prompt_to_sql_model import PromptToSQLModel
from infrastructure.gpt4 import GPT4
import re


class LLMToSQL(PromptToSQLModel):   
    def __init__(self, llm: LLM, db_schema: Optional[str] = None) -> None:
        self.system_prompt = "You are a helpful assistant designed to output only valid SQL queries. Ensure that the query is valid and answers the question."
        
        self.user_prompt_template = "Write a SQL query that answer this question:\n{question}."
        if db_schema:
            self.user_prompt_template += f"\nUse this database schema:\n{db_schema}."
        self.llm = llm
    
    def to_sql(self, prompt: str) -> str:
        response = self.llm.chat(self.user_prompt_template.format(question=prompt), self.system_prompt)
        regex_pattern = r"```sql([\s\S]*)```"
        match = re.search(regex_pattern, response)
        if match:
            return match.group(1)
        return response
            # Handle the case when no SQL query is found
        # if response.startswith("```sql"):
        #     # remove formatting
        #     response = "\n".join(response.split("\n")[1:-1])
        # return response