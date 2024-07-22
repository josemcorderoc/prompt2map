from typing import Protocol

import folium

from application.interfaces.streamlit_map import StreamlitMap


class PromptMapper(Protocol):
    def generate(self, question: str) -> StreamlitMap:
        ...