from typing import Protocol

import folium


class QuestionMapper(Protocol):
    def generate(self, question: str) -> folium.Map:
        ...