from typing import Protocol

import numpy as np


class Embedding(Protocol):
    def get_embedding(self, text: str) -> np.ndarray:
        ...
    