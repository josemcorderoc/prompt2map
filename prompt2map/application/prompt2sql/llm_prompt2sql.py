import re

from prompt2map.interfaces.nlp.llm import LLM
from prompt2map.interfaces.sql.prompt2sql import Prompt2SQL


class LLMPrompt2SQL(Prompt2SQL):
    def __init__(self, llm: LLM, db_schema: str) -> None:
        self.llm = llm
        self.system_prompt = "You are a helpful assistant designed to receive a question as input and return" \
        " a valid SQL query that retrieves the data to answer that question. Always use GROUP BY. Do not use " \
        f"integer literals. Use the following database schema as basis:\n<schema>{db_schema}</schema>"
        self.user_prompt_template = "Write a SQL query that answer this question :\n<question>{question}</question>"
        

    def to_sql(self, prompt: str) -> str:
        response = self.llm.chat(self.user_prompt_template.format(
            question=prompt), self.system_prompt)
        regex_pattern = r"```sql([\s\S]*)```"
        match = re.search(regex_pattern, response)
        if match:
            return match.group(1)
        return response
