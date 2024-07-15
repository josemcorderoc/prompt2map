from typing import Protocol


class TextSimilarity(Protocol):
    def __call__(self, text1: str, text2: str) -> float:
        ...
        
    def most_similar(self, text: str, texts: list[str]) -> str:
        ...