
import numpy as np
from openai import OpenAI

from application.interfaces.embedding import Embedding


class OpenAIEmbedding(Embedding):
    def __init__(self, model_name='text-embedding-3-small'):
        self.model_name = model_name
        self.client = OpenAI()
    
    def generate(self, text: str) -> np.ndarray:
        embedding = self.client.embeddings.create(
            input=[text],
            model=self.model_name
        ).data[0].embedding
        return np.array(embedding)
