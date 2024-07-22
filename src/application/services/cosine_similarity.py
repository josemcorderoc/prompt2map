
from scipy import spatial

from application.interfaces.embedding import Embedding
from application.interfaces.text_similarity import TextSimilarity


class CosineSimilarity(TextSimilarity):
    def __init__(self, embedding: Embedding) -> None:
        self.embedding = embedding
        
    def __call__(self, text1: str, text2: str) -> float:
        emb1 = self.embedding.get_embedding(text1)
        emb2 = self.embedding.get_embedding(text2)
        return 1 - spatial.distance.cosine(emb1, emb2).item()

    def most_similar(self, text: str, texts: list[str]) -> str:
        similarities = [self(text, t) for t in texts]
        max_index = similarities.index(max(similarities))
        return texts[max_index]
        