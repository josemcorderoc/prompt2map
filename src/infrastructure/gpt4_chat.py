from openai import OpenAI


class GPT4Chat:
    def __init__(self) -> None:
        self.client = OpenAI()
        
    def chat(self, user_prompt: str, system_prompt="You are a helpful assistant designed to output SQL.") -> str:
        response = self.client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "text" },
        messages=[
            {"role": "system", "content": system_prompt },
            {"role": "user", "content": user_prompt}
        ])
        output = response.choices[0].message.content
        if output:
            return output
        raise ValueError("No response from GPT4Chat")