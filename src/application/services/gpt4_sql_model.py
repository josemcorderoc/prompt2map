from typing import Optional
from infrastructure.gpt4_chat import GPT4Chat
from application.interfaces.sql_model import SQLModel


class GPT4SQLModel(SQLModel):   
    def __init__(self, chatbot: GPT4Chat, db_schema: Optional[str] = None) -> None:
        self.user_prompt_template = "Write a SQL query that answer this question:\n{question}."
        self.system_prompt = "You are a helpful assistant designed to output only valid SQL queries."
        if db_schema:
            self.system_prompt += f" Use the following database schema, ensure your response is a valid query:\n{db_schema}."
        self.chatbot = chatbot
    
    def to_sql(self, prompt: str) -> str:
        return self.chatbot.chat(self.user_prompt_template.format(question=prompt), self.system_prompt)