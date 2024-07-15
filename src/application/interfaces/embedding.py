from typing import Protocol

import numpy as np


class Embedding(Protocol):
    def generate(self, text: str) -> np.ndarray:
        ...
    