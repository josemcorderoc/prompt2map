from typing import Protocol


class Map(Protocol):
    def show(self) -> None:
        ...
    
    def save_image(self) -> None:
        ... 
        
    def save_html(self) -> None:
        ... 
        